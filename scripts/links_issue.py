#!/usr/bin/env python3
"""Body of the "Broken links" issue, from the lychee report and the issue's previous body.

A link that fails twice in a row is listed first, to be checked by a person. A link that fails
once is listed below: from the machines of GitHub, many sites time out, reset the connection or
answer 503 for a day, and answer again the next week.

Usage: links_issue.py REPORT [PREVIOUS_BODY] > body.md
"""
import re
import sys

LINE = re.compile(r"^\* \[[^\]]+\] <(?P<url>[^>]+)> \(at (?P<at>\d+:\d+)\) \| (?P<why>.*)$")
FILE = re.compile(r"^### (?:Errors|Timeouts) in (?P<file>\S+)")
LIMIT = 60000   # an issue body holds 65536 characters at most


def failures(text):
    """{url: (file, position, reason)} for each failing link, first place only."""
    out, file = {}, "?"
    for line in text.splitlines():
        if m := FILE.match(line):
            file = m["file"]
        elif m := LINE.match(line):
            out.setdefault(m["url"], (file, m["at"], m["why"]))
    return out


def body(report, previous=""):
    now = failures(report)
    before = set(re.findall(r"<(https?://[^>]+)>", previous))
    twice = [u for u in now if u in before]
    once = [u for u in now if u not in before]
    out = [f"{len(now)} links failed in the last run. Some sites refuse the machines of GitHub but open in a browser: "
           "open a link in a browser before changing its entry.", ""]
    for title, urls in (("Failed twice in a row: check these", twice),
                        ("Failed in this run only: checked again next week", once)):
        if urls:
            out += [f"## {title}", ""]
            out += [f"* <{u}> ({now[u][0]} {now[u][1]}) | {now[u][2]}" for u in sorted(urls, key=lambda u: now[u][:2])]
            out.append("")
    text = "\n".join(out)
    return text if len(text) <= LIMIT else text[:LIMIT].rsplit("\n", 1)[0] + "\n\n(cut: too long for an issue)\n"


if __name__ == "__main__":
    report = open(sys.argv[1], encoding="utf-8").read()
    previous = open(sys.argv[2], encoding="utf-8").read() if len(sys.argv) > 2 else ""
    sys.stdout.write(body(report, previous))
