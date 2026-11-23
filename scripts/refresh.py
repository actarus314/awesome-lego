#!/usr/bin/env python3
"""Refresh automatic metrics in data/metrics.json (standard library only).

- GitHub repositories (`github`): stars, archived flag, date of the last push (API, GITHUB_TOKEN if set).
- YouTube channels (`youtube_channel_id`): date of the last video (public RSS feed).
- Subreddits (`subreddit`) and sites with a `feed`: date of the newest item (public RSS or Atom feed).
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


def main():
    old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    new, failed, archived, stale, unfeature = {}, [], [], [], []
    token = os.environ.get("GITHUB_TOKEN")
    for path in sorted((ROOT / "data").glob("*.toml")):
        for r in tomllib.load(open(path, "rb")).get("resource", []):
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
                    m["last_activity"] = newest_date(get(f"https://www.reddit.com/r/{r['subreddit']}/new/.rss"))
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
    if stale:
        lines.append("- Not checked by hand for more than a year : " + ", ".join(stale))
    if failed:
        lines.append("- Read failures (previous values kept) : " + ", ".join(failed))
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
