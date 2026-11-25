#!/usr/bin/env python3
"""Refresh automatic metrics in data/metrics.json (standard library only).

- GitHub repositories (`github`): stars, archived flag, date of the last push (API, GITHUB_TOKEN if set).
- YouTube channels (`youtube_channel_id`): date of the last video (public RSS feed).
- Subreddits (`subreddit`): date of the newest post (public Arctic Shift archive, else Reddit's feed).
- Sites with a `feed`: date of the newest item (public RSS or Atom feed).
Reads run in parallel (subreddits one at a time, the archive asks for it). A failed read keeps the previous
values, taken from the published website when they are newer than the repository's copy. With `--from-site`
(builds that follow a push), nothing is read: the measurements of the published website are reused, and a
full reading runs only if the website cannot be reached. Writes a Markdown report to stdout: entries that failed,
became archived, left the conditions of the README selection, or were not checked by hand for more than 365 days.

With `--month [--previous FILE] [--links FILE]` (the Data report workflow, the 4th of each month), the report is the
body of the "Monthly data report" issue, read by the monthly review the next day: how long each read failure and each
ineligibility has lasted, what changed during the month (daily measurements kept on the `history` branch), the links
that block the machines of GitHub (the links issue, FILE), and a guard line at the top for what the previous report
(FILE) already listed.
"""
import datetime as dt
import json
import os
import pathlib
import re
import sys
import time
import tomllib
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import trends  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "metrics.json"
UA = "awesome-lego-refresh/1.0 (+https://github.com/actarus314/awesome-lego)"
TODAY = dt.date.today()
SITE_DATA = "https://actarus314.github.io/awesome-lego/data.json"
IDLE_DAYS = 183   # an entry of regime activity is no longer eligible for the selection after 6 months without activity
LIMIT = 60000   # body of the monthly report: the rest of the issue, trends included, must fit in 65536 characters


def site_metrics():
    """Measurements of the published website, by entry id (None if the website cannot be read)."""
    try:
        rows = json.loads(get(SITE_DATA))["resources"]
    except Exception:
        return None
    return {r["id"]: r["metrics"] for r in rows if r.get("metrics")}


def get(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def newest_date(xml_bytes):
    root = ET.fromstring(xml_bytes)
    dates = []
    for el in root.iter():
        tag = el.tag.rsplit("}", 1)[-1]
        if tag in ("published", "updated", "pubDate", "date") and el.text:
            t = el.text.strip()
            m = re.match(r"(\d{4}-\d{2}-\d{2})", t)
            if m:
                dates.append(m.group(1))
                continue
            try:
                dates.append(dt.datetime.strptime(t[:25].strip(), "%a, %d %b %Y %H:%M:%S").date().isoformat())
            except ValueError:
                pass
    dates = [d for d in dates if d <= TODAY.isoformat()]
    return max(dates) if dates else None


def subreddit_last(name):
    """Newest post of a subreddit, from the public Arctic Shift archive (Reddit refuses automated reads and
    announced the end of its feeds); Reddit's own feed only as a fallback. About one request per second."""
    url = f"https://arctic-shift.photon-reddit.com/api/posts/search?subreddit={name}&limit=1&sort=desc&fields=created_utc"
    for attempt in range(2):
        time.sleep(1 + 4 * attempt)  # the archive answers "slow down" under load
        try:
            d = json.loads(get(url))["data"]
            return dt.datetime.fromtimestamp(d[0]["created_utc"], dt.timezone.utc).date().isoformat() if d else None
        except Exception:
            pass
    return newest_date(get(f"https://www.reddit.com/r/{name}/new/.rss"))


def selected(r):
    """In the README selection: the rank 1 worldwide of the entry's group ("rank 1 of its group", decision of
    24/11/2026 at 13:02; `featured` until lot 3b)."""
    return (r.get("rank") or {}).get("intl") == 1


def regime(r, category):
    """Same rule as scripts/build.py: the entry's regime, else its group's, else activity."""
    group = next((g for g in category.get("groups", []) if g["id"] == r.get("group")), {})
    return r.get("regime") or group.get("regime") or "activity"


def score(r, last):
    """Fixed yardstick for the README selection, 0 to 7; reported, never shown on the website.
    Activity (0-3; for an operating entry, how recent its check; a finished work 2) + confidence (0-2)
    + sources read at the source (0-2). The selection is the best worldwide of each group (rank 1 intl, lot 3b):
    serving a French reader no longer counts."""
    if r.get("_regime", "activity") == "operating":
        last = str(r.get("checked") or "")  # open or closed: what counts is a recent check at the source
    days = (TODAY - dt.date.fromisoformat(last)).days if last else None
    act = 0 if days is None else 3 if days <= 30 else 2 if days <= 90 else 1 if days <= IDLE_DAYS else 0
    if r.get("_regime") == "work":
        act = 2  # a finished work does not age by its date; its review keeps it or archives it
    conf = {"high": 2, "medium": 1}.get(r.get("confidence"), 0)
    src = min(2, sum(1 for x in r.get("sources", []) if x.get("kind") in ("official", "read")))
    return act + conf + src


def selection_check(rows):
    """Per group: a selected entry that scores 2 or more below the best unselected one."""
    out, groups = [], {}
    for r, last in rows:
        groups.setdefault((r["_cat"], r["group"]), []).append((score(r, last), r))
    for (cat, g), items in sorted(groups.items()):
        out_best = max((x for x in items if not selected(x[1]) and x[1].get("status") == "active"), default=None, key=lambda x: x[0])
        for sc, r in items:
            if selected(r) and out_best and out_best[0] - sc >= 2:
                out.append(f"{cat}/{g}: {r['id']} ({sc}) against {out_best[1]['id']} ({out_best[0]})")
    return out


def coverage_gaps(rows):
    """Where fans are many and this directory is thin (data/backend/clubs-by-country.json)."""
    f = ROOT / "data" / "backend" / "clubs-by-country.json"
    if not f.exists():
        return []
    n = json.loads(f.read_text(encoding="utf-8"))["countries"]
    entries = {}
    for r, _ in rows:
        for c in r.get("countries", []):
            entries[c] = entries.get(c, 0) + 1
    return [f"{c} ({entries.get(c, 0)} entries, {k} communities)" for c, k in sorted(n.items(), key=lambda x: -x[1])
            if k >= 3 and entries.get(c, 0) <= k]


def reliability(rows):
    """Per category: share of entries by confidence and share of sources by kind (the directory's own reliability)."""
    kinds = ("official", "read", "indexed", "third-party", "forum")
    by = {}
    for r, _ in rows:
        c = by.setdefault(r["_cat"], {"n": 0, "conf": {}, "src": {}})
        c["n"] += 1
        c["conf"][r.get("confidence")] = c["conf"].get(r.get("confidence"), 0) + 1
        for x in r.get("sources", []):
            c["src"][x.get("kind")] = c["src"].get(x.get("kind"), 0) + 1
    pct = lambda a, b: f"{round(100 * a / b)} %" if b else "-"
    out = ["| Category | Entries | High | Medium | Low | " + " | ".join(k.capitalize() for k in kinds) + " |",
           "|---|---:|---:|---:|---:|" + "---:|" * len(kinds)]
    tot = {"n": 0, "conf": {}, "src": {}}
    for cat, c in sorted(by.items(), key=lambda x: -x[1]["n"]) + [("**All**", None)]:
        c = c or tot
        ns = sum(c["src"].values())
        out.append(f"| {cat} | {c['n']} | " + " | ".join(pct(c["conf"].get(k, 0), c["n"]) for k in ("high", "medium", "low")) + " | "
                   + " | ".join(pct(c["src"].get(k, 0), ns) for k in kinds) + " |")
        if c is not tot:
            tot["n"] += c["n"]
            for part in ("conf", "src"):
                for k, v in c[part].items():
                    tot[part][k] = tot[part].get(k, 0) + v
    return out


def read(r, old, token):
    """One entry's measurements: (metrics or None when the entry has nothing to read, error or None)."""
    m = dict(old.get(r["id"], {}))
    try:
        if r.get("github"):
            h = {"Accept": "application/vnd.github+json"}
            if token:
                h["Authorization"] = f"Bearer {token}"
            d = json.loads(get(f"https://api.github.com/repos/{r['github']}", h))
            m.update(stars=d["stargazers_count"], archived=d["archived"], last_activity=d["pushed_at"][:10])
        elif r.get("youtube_channel_id"):
            m["last_activity"] = newest_date(get(f"https://www.youtube.com/feeds/videos.xml?channel_id={r['youtube_channel_id']}"))
        elif r.get("subreddit"):
            m["last_activity"] = subreddit_last(r["subreddit"])
        elif r.get("feed"):
            m["last_activity"] = newest_date(get(r["feed"]))
        else:
            m = None
        if m is not None:
            m["refreshed"] = TODAY.isoformat()
    except Exception as exc:  # network, parsing: keep previous values
        return m, f"{r['id']}: {type(exc).__name__}"
    return m, None


def date_en(day):
    """A date as the website and the reports write it: "24 Nov 2026" (a date or an ISO string; months abbreviated)."""
    d = dt.date.fromisoformat(day) if isinstance(day, str) else day
    return f"{d.day} {'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()[d.month - 1]} {d.year}"


def since(iso):
    """'since 12 November 2026, 22 days' for a past ISO date."""
    return f"since {date_en(iso)}, {day_count(iso)}"


def day_count(iso):
    n = (TODAY - dt.date.fromisoformat(iso)).days
    return f"{n} day" if n == 1 else f"{n} days"


def month_changes(days, ids):
    """What changed during the month in the daily measurements of the `history` branch: (heading line, items)."""
    if days is None:
        return "The `history` branch could not be read this month.", []
    if not days:
        return "No measurements kept on the `history` branch yet.", []
    names = list(days)
    start = max((d for d in names if d <= (TODAY - dt.timedelta(days=30)).isoformat()), default=names[0])
    a, b = days[start], days[names[-1]]
    items = []
    moved = [f"{i}: {trends.status(a[i].get('last_activity'), start)} → {trends.status(b[i].get('last_activity'), names[-1])}"
             for i in sorted(set(a) & set(b)) if trends.status(a[i].get("last_activity"), start) != trends.status(b[i].get("last_activity"), names[-1])
             and trends.status(a[i].get("last_activity"), start) and trends.status(b[i].get("last_activity"), names[-1])]
    newly = [i for i in sorted(set(a) & set(b)) if b[i].get("archived") and not a[i].get("archived")]
    came = sorted(set(b) - set(a))
    left = sorted(i for i in set(a) - set(b) if i in ids)   # an entry removed from the data is not a change of the month
    for label, xs in (("Status changes (active up to 6 months, slow up to 12, then inactive)", moved),
                      ("Archived on GitHub during the month", newly), ("Measured for the first time", came),
                      ("No longer measured though still in the data", left)):
        items.append(f"- {label}: {', '.join(xs) or 'none'}")
    return (f"From {date_en(start)} to {date_en(names[-1])}; {len(days)} day{'s' * (len(days) > 1)} kept on the `history` branch"
            + (" (fewer than 30: the month is partly covered)." if len(days) < 30 else ".")), items


def archived_since(days, i):
    """First day of the last unbroken run of `archived` in the history, with 'at least' when it starts the history."""
    run = None
    for d, m in (days or {}).items():
        run = (run or d) if (m.get(i) or {}).get("archived") else None
    if not run:
        return None
    return ("at least " if run == next(iter(days)) else "") + since(run)


def links_blocking(text):
    """The links that block GitHub, from the body of the links issue (scripts/links_issue.py)."""
    m = re.search(r"<summary>(They block GitHub[^<]*)</summary>(.*?)</details>", text or "", re.S)
    return (m.group(1), [l for l in m.group(2).strip().splitlines() if l.startswith("* ")]) if m else (None, [])


def report_ids(previous):
    """The items listed by a monthly report, kept in its last line: {"month", "date", "ids", "base"}."""
    m = re.search(r"<!-- report-ids (\{.*?\}) -->", previous or "")
    try:
        return json.loads(m.group(1)) if m else {}
    except ValueError:
        return {}


def guard(previous, ids):
    """(date of the report compared with, {kind: [ids]} of this report already listed there, base to keep).
    A report written again in the same month (a run started by hand) compares with the report it replaces had as
    its own base, so that the guard always looks one month back."""
    prev = report_ids(previous)
    base = prev.get("base") if prev.get("month") == TODAY.isoformat()[:7] else prev
    base = {k: base[k] for k in ("month", "date", "ids") if k in base} if base else {}
    before = base.get("ids", {})
    kept = {k: sorted(set(v) & set(before.get(k, []))) for k, v in ids.items() if set(v) & set(before.get(k, []))}
    return base.get("date"), kept, base


def arg(name):
    return pathlib.Path(sys.argv[sys.argv.index(name) + 1]).read_text(encoding="utf-8") if name in sys.argv and sys.argv.index(name) + 1 < len(sys.argv) else ""


def main():
    old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    site = site_metrics()
    if "--from-site" in sys.argv and site:
        OUT.write_text(json.dumps(site, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(f"Measurements reused from the published website: {len(site)}")
        return 0
    for k, v in (site or {}).items():  # the published values are newer than the repository's copy
        if v.get("refreshed", "") >= old.get(k, {}).get("refreshed", ""):
            old[k] = v
    month = "--month" in sys.argv
    days = {}
    if month:
        try:
            days = trends.snapshots()
        except Exception:
            days = None   # never loses the rest of the report; said in its section
    new, failed, archived, stale, unfeature = {}, [], [], [], []
    token = os.environ.get("GITHUB_TOKEN")
    entries = [dict(r, _cat=path.stem, _regime=regime(r, d.get("category", {}))) for path in sorted((ROOT / "data").glob("*.toml"))
               for d in [tomllib.loads(pathlib.Path(path).read_text(encoding="utf-8"))] for r in d.get("resource", [])]
    with ThreadPoolExecutor(12) as pool, ThreadPoolExecutor(1) as slow:  # network waits overlap; subreddits stay one at a time
        jobs = [(slow if r.get("subreddit") and not r.get("github") and not r.get("youtube_channel_id") else pool).submit(read, r, old, token) for r in entries]
        results = [j.result() for j in jobs]
    rows = []
    for r, (m, err) in zip(entries, results):
        if err:
            ok = (old.get(r["id"]) or {}).get("refreshed")
            failed.append((r["id"], err.split(": ", 1)[1], f"last read {date_en(ok)}, {day_count(ok)} ago" if ok else "never read"))
        if m and m.get("archived") and r.get("status") != "archived":
            archived.append(r["id"])
        if m:
            new[r["id"]] = {k: v for k, v in m.items() if v is not None}
        last = (new.get(r["id"]) or {}).get("last_activity") or str(r.get("last_activity") or "")
        idle = r["_regime"] == "activity" and last and (TODAY - dt.date.fromisoformat(last)).days > IDLE_DAYS
        gone = (new.get(r["id"]) or {}).get("archived")
        if selected(r) and (idle or gone or r.get("status") != "active" or r.get("confidence") == "low"):
            why = []
            if idle:
                why.append("inactive " + since((dt.date.fromisoformat(last) + dt.timedelta(days=IDLE_DAYS + 1)).isoformat()) if month else f"last activity {date_en(last)}")
            if gone:
                why.append("archived " + (archived_since(days, r["id"]) or "on GitHub") if month else "archived")
            if r.get("status") != "active":
                why.append(f"status {r.get('status')}")
            if r.get("confidence") == "low":
                why.append("low confidence")
            unfeature.append((r["id"], "; ".join(why)))
        rows.append((r, last or None))
        checked = str(r.get("checked", ""))
        if checked and (TODAY - dt.date.fromisoformat(checked)).days > 365:
            stale.append(f"{r['id']} ({date_en(checked)})")
    OUT.write_text(json.dumps(new, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    lines = [f"Monthly data report: {date_en(TODAY.isoformat())}. Read by the monthly review." if month
             else f"Automatic refresh: {date_en(TODAY)}", ""]
    ids = {"read failures": [i for i, _, _ in failed], "no longer eligible": [i for i, _ in unfeature], "archived": archived}
    if month:
        when, kept, base = guard(arg("--previous"), ids)
        lines += [("**Guard: still listed since the report of " + (when or "last month") + ":** "
                   + "; ".join(f"{k}: {', '.join(v)}" for k, v in kept.items())) if kept
                  else "**Guard:** nothing carried over from the previous report.", ""]
    lines.append(f"- Measured: {len(new)}")
    if archived:
        lines.append("- Archived on GitHub, to review: " + ", ".join(archived))
    if unfeature:
        lines.append("- In the README selection but no longer eligible (inactive for 6 months, archived or weak source), to remove from the selection: "
                     + ", ".join(f"{i} ({why})" for i, why in unfeature))
    gaps = coverage_gaps(rows)
    if gaps:
        lines.append("- Coverage gaps (countries with 3 or more fan communities recognized by LEGO and at most one entry per community): " + ", ".join(gaps))
    swaps = selection_check(rows)
    if swaps:
        lines.append("- Selection check (score out of 7: activity, confidence, sources read), selected entry far below an unselected one of its group: " + "; ".join(swaps))
    if stale:
        lines.append("- Not checked by hand for more than a year: " + ", ".join(stale))
    if failed:
        lines.append("- Read failures (previous values kept): " + ", ".join(f"{i}: {why} ({when})" for i, why, when in failed))
    if month:
        head, items = month_changes(days, {r["id"] for r in entries})
        lines += ["", "### Changes during the month", "", head, *([""] + items if items else [])]
        title, blocking = links_blocking(arg("--links"))
        lines += ["", "### Links that block GitHub", "",
                  *((f"{title}, from the links issue:", "", *blocking) if blocking
                    else ("None listed in the links issue." if arg("--links").strip() else "No links issue found.",))]
    lines += ["", "### Reliability of the directory", "",
              "Confidence of the entries (high: read at the source; medium: indexed or third-party; low: single weak source) and kinds of their sources, per category.", "",
              *reliability(rows)]
    if month:
        lines += ["", "<!-- report-ids " + json.dumps({"month": TODAY.isoformat()[:7], "date": date_en(TODAY), "ids": ids, "base": base},
                                                      sort_keys=True, ensure_ascii=False) + " -->"]
    text = "\n".join(lines)
    if len(text) > LIMIT:   # an issue body holds 65536 characters at most; the ids line stays
        tail = text[text.rindex("<!-- report-ids"):] if month else ""
        text = text[: LIMIT - len(tail) - 40].rsplit("\n", 1)[0] + "\n\n(cut: too long for an issue)\n\n" + tail
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
