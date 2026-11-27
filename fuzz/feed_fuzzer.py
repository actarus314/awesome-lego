#!/usr/bin/env python3
"""Fuzz target: an RSS or Atom feed of a third-party site (scripts/refresh.py, newest_date).

Pages reads the feeds of the entries every day, and the review pass reads the feeds it finds
(scripts/discover_feeds.py), with the same function. Its callers count any exception as a read failure, so an
exception is expected here; what is not: a day that is not a real date of the ISO calendar or that lies in the
future (refresh.py and build.py read it with date.fromisoformat, out of any try: one feed would stop the daily
build), a run over the time limit (an expression or a loop that runs away), memory (entities that expand).

Run by hand: python3 fuzz/feed_fuzzer.py fuzz/seeds/feed -dict=fuzz/feed.dict -max_total_time=60
"""
import datetime as dt
import pathlib
import re
import sys

import atheris

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
with atheris.instrument_imports():
    import refresh  # noqa: E402

DAY = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def TestOneInput(data):
    try:
        day = refresh.newest_date(data)
    except Exception:
        return   # not a feed: a read failure in the report, as for any unreadable source
    if day is None:
        return
    if not isinstance(day, str) or not DAY.fullmatch(day):
        raise AssertionError(f"newest_date gave {day!r}, not a date written YYYY-MM-DD")
    try:
        when = dt.date.fromisoformat(day)
    except ValueError:
        raise AssertionError(f"newest_date gave {day!r}, which is no day of the calendar") from None
    if when > refresh.TODAY:
        raise AssertionError(f"newest_date gave {day!r}, a day in the future")


if __name__ == "__main__":
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()
