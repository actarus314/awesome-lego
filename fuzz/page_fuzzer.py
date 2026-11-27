#!/usr/bin/env python3
"""Fuzz target: the HTML page of a third-party site, as two scripts read it.

- scripts/links_issue.py, classify: Links opens the address of every entry and looks for a dead page that answers
  200. It is called out of any try (dead_pages): an exception there stops the weekly issue.
- scripts/discover_feeds.py, find: the review pass reads the page of an entry without a source and follows its
  <link rel="alternate"> to a feed; an exception there stops the search for every entry.
Neither may raise. classify gives None or (kind, evidence), the evidence quoting the page only as code;
find gives None or the address of a feed of the same site. Also counted: a run over the time limit, memory.

Run by hand: python3 fuzz/page_fuzzer.py fuzz/seeds/page -dict=fuzz/page.dict -max_total_time=60
"""
import pathlib
import re
import sys

import atheris

ROOT = pathlib.Path(getattr(sys, "_MEIPASS", pathlib.Path(__file__).resolve().parent.parent))   # the build bundles data/brands.toml
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
with atheris.instrument_imports():
    import discover_feeds  # noqa: E402
    import links_issue  # noqa: E402

links_issue._BRANDS[:] = links_issue.brand_words(ROOT) or ["lego"]   # the brands of the directory, as in a real run
ENTRY = {"url": "https://club.example/news/"}
KINDS = {"parked or expired", "taken over", "closed"}
OUTSIDE_CODE = re.compile(r"`[^`\n]*`")


def TestOneInput(data):
    page = data.decode("utf-8", "replace")   # as links_issue._fetch decodes a page
    found = links_issue.classify(page)
    if found is not None:
        kind, evidence = found
        if kind not in KINDS:
            raise AssertionError(f"classify gave the kind {kind!r}")
        if "`" in OUTSIDE_CODE.sub("", evidence) or "\n" in evidence:
            raise AssertionError(f"evidence {evidence!r} quotes the page outside a code span")

    discover_feeds.get = lambda url: (ENTRY["url"], data) if url == ENTRY["url"] else (url, data)   # the page, then the same bytes as every feed
    feed = discover_feeds.find(ENTRY)
    if feed is not None and not discover_feeds.belongs(ENTRY["url"], feed):
        raise AssertionError(f"find kept {feed!r}, a feed of another site")


if __name__ == "__main__":
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()
