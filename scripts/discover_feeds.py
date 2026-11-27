#!/usr/bin/env python3
"""Find a machine-readable activity source for entries that have none (standard library only).

For every entry without `github`, `youtube_channel_id`, `subreddit` or `feed`, read its page and look for
an RSS or Atom feed: the page's own <link rel="alternate"> first, then common feed addresses. A feed is
kept only if it belongs to the entry (same site; for a page of a site, that page's own feed), parses and has
at least one dated item. With --write, the `feed` field is added to the
TOML files (one line after `url`); without it, the findings are printed as JSON.
"""
import concurrent.futures as cf
import json
import pathlib
import re
import sys
import tomllib
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from refresh import newest_date  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
UA = "Mozilla/5.0 (compatible; awesome-lego-feeds/1.0; +https://github.com/actarus314/awesome-lego)"
COMMON = ["feed/", "rss", "rss.xml", "feed.xml", "atom.xml", "index.xml", "blog/feed/", "news/feed/"]
LINK = re.compile(r"<link\b[^>]*>", re.I)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.geturl(), r.read(2_000_000)


def valid(url):
    try:
        _, body = get(url)
        return newest_date(body) is not None
    except Exception:
        return False


def find(r):
    try:
        final, html = get(r["url"])
    except Exception:
        return None
    text = html.decode("utf-8", "ignore")
    cands = []
    for tag in LINK.findall(text):
        if re.search(r'rel=["\']?alternate', tag, re.I) and re.search(r"application/(rss|atom)\+xml", tag, re.I):
            m = re.search(r'href=["\']([^"\']+)', tag, re.I)
            if m and "comment" not in m.group(1).lower():
                try:
                    cands.append(urllib.parse.urljoin(final, m.group(1)))
                except ValueError:   # an address urllib cannot read ("http://[x"): the page's error, not the search's
                    pass
    cands += [urllib.parse.urljoin(final if final.endswith("/") else final + "/", c) for c in COMMON]
    for c in dict.fromkeys(cands):
        if belongs(r["url"], c) and valid(c):
            return c
    return None


def belongs(entry, feed):
    """A feed measures an entry only if it is on the same site and, for an entry that is one page of a site
    (a guide, a forum thread, a shop collection), only if the feed is that page's own feed: the site-wide
    feed of a news site says nothing about its glossary page."""
    e, f = urllib.parse.urlparse(entry), urllib.parse.urlparse(feed)
    host = lambda u: u.netloc.lower().removeprefix("www.")
    if host(e) != host(f):
        return False
    path = e.path.strip("/")
    return not path or f.path.strip("/").startswith(path)


def main():
    todo = []
    for path in sorted((ROOT / "data").glob("*.toml")):
        if path.stem == "journeys":
            continue
        for r in tomllib.loads(pathlib.Path(path).read_text(encoding="utf-8")).get("resource", []):
            if not any(r.get(k) for k in ("github", "youtube_channel_id", "subreddit", "feed")) and r.get("status") != "dead":
                todo.append((path, r))
    found = {}
    with cf.ThreadPoolExecutor(12) as ex:
        for (path, r), feed in zip(todo, ex.map(lambda t: find(t[1]), todo)):
            if feed:
                found[r["id"]] = (path, feed)
    if "--write" not in sys.argv:
        print(json.dumps({k: v[1] for k, v in found.items()}, indent=1))
        print(f"{len(found)} feeds found for {len(todo)} entries without a source", file=sys.stderr)
        return 0
    for path in {p for p, _ in found.values()}:
        s = path.read_text(encoding="utf-8")
        for rid, (p, feed) in found.items():
            if p != path:
                continue
            s = re.sub(rf'(?ms)^(id = "{re.escape(rid)}"\n.*?^url = "[^"]*"\n)', lambda m: m.group(1) + f'feed = "{feed}"\n', s, count=1)
        tomllib.loads(s)
        path.write_text(s, encoding="utf-8")
    print(f"{len(found)} feeds written for {len(todo)} entries without a source", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
