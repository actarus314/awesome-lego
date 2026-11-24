#!/usr/bin/env python3
"""Refresh automatic metrics in data/metrics.json (standard library only).

- GitHub repositories (`github`): stars, archived flag, date of the last push (API, GITHUB_TOKEN if set).
- YouTube channels (`youtube_channel_id`): date of the last video (public RSS feed).
- Subreddits (`subreddit`): date of the newest post (public Arctic Shift archive, else Reddit's feed).
- Sites with a `feed`: date of the newest item (public RSS or Atom feed).
Reads run in parallel (subreddits one at a time, the archive asks for it). A failed read keeps the previous
values, taken from the published website when they are newer than the repository's copy. With `--from-site`
(builds that follow a push), nothing is read: the measurements of the published website are reused, and a
full reading runs only if the website cannot be reached. Writes a Markdown report to stdout, used as the body of the
weekly report issue: entries that failed, became archived, left the conditions of the README
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
from concurrent.futures import ThreadPoolExecutor

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "metrics.json"
UA = "awesome-lego-refresh/1.0 (+https://github.com/actarus314/awesome-lego)"
TODAY = dt.date.today()
SITE_DATA = "https://actarus314.github.io/awesome-lego/data.json"


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


def regime(r, category):
    """Same rule as scripts/build.py: the entry's regime, else its group's, else activity."""
    group = next((g for g in category.get("groups", []) if g["id"] == r.get("group")), {})
    return r.get("regime") or group.get("regime") or "activity"


def score(r, last):
    """Fixed yardstick for the README selection, 0 to 9; reported, never shown on the website.
    Activity (0-3; for an operating entry, how recent its check; a finished work 2) + confidence (0-2)
    + sources read at the source (0-2) + serves a French reader (0-2)."""
    if r.get("_regime", "activity") == "operating":
        last = str(r.get("checked") or "")  # open or closed: what counts is a recent check at the source
    days = (TODAY - dt.date.fromisoformat(last)).days if last else None
    act = 0 if days is None else 3 if days <= 30 else 2 if days <= 90 else 1 if days <= 183 else 0
    if r.get("_regime") == "work":
        act = 2  # a finished work does not age by its date; its review keeps it or archives it
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
                failed.append(err)
            if m and m.get("archived") and r.get("status") != "archived":
                archived.append(r["id"])
            if m:
                new[r["id"]] = {k: v for k, v in m.items() if v is not None}
            last = (new.get(r["id"]) or {}).get("last_activity") or str(r.get("last_activity") or "")
            idle = r["_regime"] == "activity" and last and (TODAY - dt.date.fromisoformat(last)).days > 183
            if r.get("featured") and (idle or r.get("status") != "active" or r.get("confidence") == "low" or (new.get(r["id"]) or {}).get("archived")):
                unfeature.append(f"{r['id']} ({last or 'no date'})")
            rows.append((r, last or None))
            checked = str(r.get("checked", ""))
            if checked and (TODAY - dt.date.fromisoformat(checked)).days > 365:
                stale.append(f"{r['id']} ({checked})")
    OUT.write_text(json.dumps(new, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    lines = [f"Automatic refresh: {TODAY.isoformat()}", "",
             f"- Measured: {len(new)}"]
    if archived:
        lines.append("- Archived on GitHub, to review: " + ", ".join(archived))
    if unfeature:
        lines.append("- In the README selection but no longer eligible (inactive for 6 months, archived or weak source), to remove from the selection: " + ", ".join(unfeature))
    gaps = coverage_gaps(rows)
    if gaps:
        lines.append("- Coverage gaps (countries with 3 or more fan communities recognized by LEGO and at most one entry per community): " + ", ".join(gaps))
    swaps = selection_check(rows)
    if swaps:
        lines.append("- Selection check (score out of 9: activity, confidence, sources read, French reader), selected entry far below an unselected one of its group: " + "; ".join(swaps))
    if stale:
        lines.append("- Not checked by hand for more than a year: " + ", ".join(stale))
    if failed:
        lines.append("- Read failures (previous values kept): " + ", ".join(failed))
    lines += ["", "### Reliability of the directory", "",
              "Confidence of the entries (high: read at the source; medium: indexed or third-party; low: single weak source) and kinds of their sources, per category.", "",
              *reliability(rows)]
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
