#!/usr/bin/env python3
"""Read the daily measurements kept on the `history` branch and prepare the trends (not shown on the website yet).

Usage: python3 scripts/trends.py [--dir DIR] [--json]   (standard library only)

Without --dir, fetches the last commit of origin/history (the branch keeps one file per day, metrics/YYYY-MM-DD.json,
written by the daily Pages build) and reads it with git. Per entry measured automatically:
- posting days: how many distinct "last activity" dates were observed in a window (a new post, video, commit or
  feed item moves the date; several in one day count once), compared between the last window and the one before;
- GitHub stars gained in each window;
- status changes under the website's rule (active up to 6 months, slowing up to 12, then inactive);
- entries that appeared in or left the measurements (added to or removed from the data).
Trends need two full windows: the report says how many days are kept and from when they become meaningful.
"""
import datetime as dt
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
WINDOW = 90  # days per window; two windows are compared


def snapshots(folder=None):
    days = {}
    if folder:
        for f in sorted(pathlib.Path(folder).glob("*.json")):
            days[f.stem] = json.loads(f.read_text(encoding="utf-8"))
        return days
    git = lambda *a: subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True, check=True).stdout
    if not git("ls-remote", "origin", "history").strip():
        return days  # no history branch yet
    git("fetch", "-q", "--depth=1", "origin", "history")  # a failure here is an error, not "no measurements"
    for name in git("ls-tree", "--name-only", "FETCH_HEAD", "metrics/").split():
        if name.endswith(".json"):
            days[pathlib.Path(name).stem] = json.loads(git("show", f"FETCH_HEAD:{name}"))
    return dict(sorted(days.items()))


def status(last, day):
    if not last:
        return None
    d = (dt.date.fromisoformat(day) - dt.date.fromisoformat(last)).days
    return "active" if d <= 183 else "slow" if d <= 365 else "inactive"


def analyse(days):
    if not days:
        return {"days": 0}
    names = list(days)
    first, last = names[0], names[-1]
    span = (dt.date.fromisoformat(last) - dt.date.fromisoformat(first)).days + 1
    end = dt.date.fromisoformat(last)
    w1 = (end - dt.timedelta(days=WINDOW)).isoformat()
    w0 = (end - dt.timedelta(days=2 * WINDOW)).isoformat()
    ids = sorted({i for m in days.values() for i in m})
    out = {"days": len(days), "first": first, "last": last, "span": span,
           "ready_from": (dt.date.fromisoformat(first) + dt.timedelta(days=2 * WINDOW)).isoformat(), "entries": {}}
    for i in ids:
        series = [(d, m.get(i, {})) for d, m in days.items()]
        acts = {x.get("last_activity") for _, x in series if x.get("last_activity")}
        recent = len({a for a in acts if a > w1})
        before = len({a for a in acts if w0 < a <= w1})
        stars = [(d, x.get("stars")) for d, x in series if x.get("stars") is not None]
        gain = lambda a, b: (lambda s: s[-1][1] - s[0][1] if len(s) > 1 else None)([p for p in stars if a < p[0] <= b])
        st = [(d, status(x.get("last_activity"), d)) for d, x in series if x]
        changes = [f"{a[1]} → {b[1]} ({b[0]})" for a, b in zip(st, st[1:]) if a[1] != b[1] and a[1] and b[1]]
        present = [d for d, m in days.items() if i in m]
        out["entries"][i] = {"posting_days": [before, recent], "stars_gained": [gain(w0, w1), gain(w1, last)],
                             "status_changes": changes, "seen": [present[0], present[-1]]}
    return out


def report(a):
    if not a["days"]:
        return ["### Trends", "", "No measurements kept yet on the `history` branch."]
    ready = a["span"] >= 2 * WINDOW
    lines = ["### Trends", "", f"{a['days']} days of measurements kept, from {a['first']} to {a['last']}. "
             + ("Two windows of 90 days are available." if ready else f"Two windows of {WINDOW} days are needed: meaningful from {a['ready_from']}.")]
    if not ready:
        return lines
    e = {i: v for i, v in a["entries"].items() if v["seen"][0] == a["first"] and v["seen"][1] == a["last"]}  # measured all along: an entry that appeared or left is not a trend
    up = sorted((x for x in e.items() if x[1]["posting_days"][1] >= x[1]["posting_days"][0] + 3), key=lambda x: x[1]["posting_days"][0] - x[1]["posting_days"][1])
    down = sorted((x for x in e.items() if x[1]["posting_days"][0] >= x[1]["posting_days"][1] + 3), key=lambda x: x[1]["posting_days"][1] - x[1]["posting_days"][0])
    fmt = lambda xs: ", ".join(f"{i} ({v['posting_days'][0]} → {v['posting_days'][1]})" for i, v in xs[:15]) or "none"
    born = [i for i, v in a["entries"].items() if v["seen"][0] > a["first"]]
    gone = [i for i, v in a["entries"].items() if v["seen"][1] < a["last"]]
    lines += [f"- More posting days than the window before: {fmt(up)}", f"- Fewer posting days: {fmt(down)}",
              f"- Status changes: {', '.join(f'{i}: {c[-1]}' for i, v in e.items() for c in [v['status_changes']] if c) or 'none'}",
              f"- Appeared in the measurements: {', '.join(born) or 'none'}", f"- Left the measurements: {', '.join(gone) or 'none'}"]
    return lines


def main():
    folder = sys.argv[sys.argv.index("--dir") + 1] if "--dir" in sys.argv else None
    a = analyse(snapshots(folder))
    print(json.dumps(a, ensure_ascii=False, indent=1) if "--json" in sys.argv else "\n".join(report(a)))


if __name__ == "__main__":
    main()
