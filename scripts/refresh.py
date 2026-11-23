#!/usr/bin/env python3
"""Refresh automatic metrics in data/metrics.json (standard library only).

- GitHub repositories (`github`): stars, archived flag, date of the last push (API, GITHUB_TOKEN if set).
- YouTube channels (`youtube_channel_id`): date of the last video (public RSS feed).
- Subreddits (`subreddit`): date of the newest post (public Arctic Shift archive, else Reddit's feed).
- Sites with a `feed`: date of the newest item (public RSS or Atom feed).
A failed read keeps the previous values. Writes a Markdown report to stdout, used as the body of the
weekly pull request: entries that failed, became archived, left the conditions of the README
selection, or were not checked by hand for more than 365 days.
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

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "metrics.json"
UA = "awesome-lego-refresh/1.0 (+https://github.com/actarus314/awesome-lego)"
TODAY = dt.date.today()


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


def score(r, last):
    """Fixed yardstick for the README selection, 0 to 9; reported, never shown on the website.
    Activity (0-3) + confidence (0-2) + sources read at the source (0-2) + serves a French reader (0-2)."""
    days = (TODAY - dt.date.fromisoformat(last)).days if last else None
    act = 0 if days is None else 3 if days <= 30 else 2 if days <= 90 else 1 if days <= 183 else 0
    conf = {"high": 2, "medium": 1}.get(r.get("confidence"), 0)
    src = min(2, sum(1 for x in r.get("sources", []) if x.get("kind") in ("official", "read")))
    fr = ("fr" in r.get("languages", [])) + ("FR" in r.get("countries", []) or bool(r.get("ships_to_france")))
    return act + conf + src + fr


def selection_check(rows):
    """Per group: a selected entry that scores 2 or more below the best unselected one."""
    out, groups = [], {}
    for r, last in rows:
        groups.setdefault((r["_cat"], r["group"]), []).append((score(r, last), r))
    for (cat, g), items in sorted(groups.items()):
        out_best = max((x for x in items if not x[1].get("featured") and x[1].get("status") == "active"), default=None, key=lambda x: x[0])
        for sc, r in items:
            if r.get("featured") and out_best and out_best[0] - sc >= 2:
                out.append(f"{cat}/{g}: {r['id']} ({sc}) vs {out_best[1]['id']} ({out_best[0]})")
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


def main():
    old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    new, failed, archived, stale, unfeature = {}, [], [], [], []
    token = os.environ.get("GITHUB_TOKEN")
    rows = []
    for path in sorted((ROOT / "data").glob("*.toml")):
        for r in tomllib.load(open(path, "rb")).get("resource", []):
            r["_cat"] = path.stem
            m = dict(old.get(r["id"], {}))
            try:
                if r.get("github"):
                    h = {"Accept": "application/vnd.github+json"}
                    if token:
                        h["Authorization"] = f"Bearer {token}"
                    d = json.loads(get(f"https://api.github.com/repos/{r['github']}", h))
                    m.update(stars=d["stargazers_count"], archived=d["archived"], last_activity=d["pushed_at"][:10])
                    if d["archived"] and r.get("status") != "archived":
                        archived.append(r["id"])
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
                failed.append(f"{r['id']}: {type(exc).__name__}")
            if m:
                new[r["id"]] = {k: v for k, v in m.items() if v is not None}
            last = (new.get(r["id"]) or {}).get("last_activity") or str(r.get("last_activity") or "")
            idle = last and (TODAY - dt.date.fromisoformat(last)).days > 183
            if r.get("featured") and (idle or r.get("status") != "active" or r.get("confidence") == "low" or (new.get(r["id"]) or {}).get("archived")):
                unfeature.append(f"{r['id']} ({last or 'no date'})")
            rows.append((r, last or None))
            checked = str(r.get("checked", ""))
            if checked and (TODAY - dt.date.fromisoformat(checked)).days > 365:
                stale.append(f"{r['id']} ({checked})")
    OUT.write_text(json.dumps(new, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    lines = [f"Automatic refresh : {TODAY.isoformat()}", "",
             f"- Measured : {len(new)}"]
    if archived:
        lines.append("- Archived on GitHub, to review : " + ", ".join(archived))
    if unfeature:
        lines.append("- In the README selection but no longer eligible (inactive for 6 months, archived or weak source), to remove from the selection : " + ", ".join(unfeature))
    gaps = coverage_gaps(rows)
    if gaps:
        lines.append("- Coverage gaps (countries with 3 or more fan communities recognized by LEGO and at most one entry per community) : " + ", ".join(gaps))
    swaps = selection_check(rows)
    if swaps:
        lines.append("- Selection check (score out of 9: activity, confidence, sources read, French reader), selected entry far below an unselected one of its group : " + "; ".join(swaps))
    if stale:
        lines.append("- Not checked by hand for more than a year : " + ", ".join(stale))
    if failed:
        lines.append("- Read failures (previous values kept) : " + ", ".join(failed))
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
