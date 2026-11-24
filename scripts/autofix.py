#!/usr/bin/env python3
"""Mechanical data fixes, proposed weekly as a pull request (standard library only).

- An address that moved for good (every hop a 301 or 308 redirect, final page answers 200) is replaced by
  its new address. Temporary redirects (302, 303, 307: language, country or login pages) are left alone.
- A `next_date` already past is removed: the next edition is unknown until someone reads it.
Prints a Markdown summary; with --write, edits the TOML files in place.
"""
import concurrent.futures as cf
import datetime as dt
import pathlib
import re
import sys
import tomllib
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
UA = "Mozilla/5.0 (compatible; awesome-lego-autofix/1.0; +https://github.com/actarus314/awesome-lego)"
TODAY = dt.date.today().isoformat()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def moved(url):
    """New address if the page moved permanently, else None."""
    cur, hops = url, 0
    while hops < 5:
        req = urllib.request.Request(cur, headers={"User-Agent": UA}, method="GET")
        try:
            with OPENER.open(req, timeout=15) as r:
                code = r.status
        except urllib.error.HTTPError as e:
            code = e.code
            if code in (301, 308) and e.headers.get("Location"):
                cur = urllib.parse.urljoin(cur, e.headers["Location"])
                hops += 1
                continue
            return None
        except Exception:
            return None
        break
    if not hops or code != 200 or "?" in cur or not re.fullmatch(r"https?://[^\s\"\\<>`]+", cur):
        return None  # an address with characters that would break the data file or the pull request is left to a person
    same = lambda a, b: a.rstrip("/").lower() == b.rstrip("/").lower()
    return None if same(cur, url) or same(cur.replace("http://", "https://"), url) else cur


def main():
    write = "--write" in sys.argv
    urls, dates, files = {}, [], {}
    for path in sorted((ROOT / "data").glob("*.toml")):
        if path.stem == "journeys":
            continue
        files[path] = path.read_text(encoding="utf-8")
        for r in tomllib.loads(files[path]).get("resource", []):
            urls[r["id"]] = (path, r["url"])
            if r.get("next_date") and str(r["next_date"]) < TODAY:
                dates.append((path, r["id"], str(r["next_date"])))
    with cf.ThreadPoolExecutor(12) as ex:
        new = dict(zip(urls, ex.map(lambda k: moved(urls[k][1]), urls)))
    lines = []
    for rid, nu in sorted(new.items()):
        if not nu:
            continue
        path, old = urls[rid]
        host = lambda u: urllib.parse.urlsplit(u).hostname.removeprefix("www.")
        flag = "**other site, check the owner**: " if host(old) != host(nu) else ""  # a moved address can hide a change of owner
        lines.append(f"- `{rid}`: {flag}address moved for good, `{old}` → `{nu}`")
        files[path] = re.sub(rf'(?ms)^(id = "{re.escape(rid)}"\n.*?^url = )"{re.escape(old)}"', lambda m: m.group(1) + f'"{nu}"', files[path], count=1)
    for path, rid, d in dates:
        lines.append(f"- `{rid}`: next edition date {d} is past, removed")
        files[path] = re.sub(rf'(?ms)^(id = "{re.escape(rid)}"\n.*?)^next_date = [^\n]*\n', r"\1", files[path], count=1)
    if write:
        for path, text in files.items():
            tomllib.loads(text)
            if text != path.read_text(encoding="utf-8"):
                path.write_text(text, encoding="utf-8")
    lines.sort(key=lambda l: "**" not in l)  # changes of site first, for the person who merges
    print("\n".join(lines) if lines else "Nothing to fix.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
