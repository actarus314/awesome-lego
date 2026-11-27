#!/usr/bin/env python3
"""Fuzz target: what the probes of Globalping bring back from third-party servers (scripts/links_issue.py).

Links opens again from Globalping every link that failed from GitHub (recheck), follows the redirects the
probes report and writes the issue Broken links (body). The probes are volunteers' machines and the servers
are anyone's: status codes, headers (Location), raw output and page bodies are the fuzzer's here, in the shape
that the Globalping API documents (https://globalping.io/docs/api.globalping.io); the API itself is replaced by
a fake. Nothing there may raise (main calls both out of any try). Checked: every verdict is one the issue knows,
and the body of the issue quotes third-party text only as code (no mention, link or markup can come alive).
Also counted: a run over the time limit, memory.

Run by hand: python3 fuzz/globalping_fuzzer.py -dict=fuzz/globalping.dict -max_total_time=60
"""
import datetime as dt
import pathlib
import re
import sys
import urllib.error

import atheris

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
with atheris.instrument_imports():
    import links_issue  # noqa: E402

links_issue._BRANDS[:] = ["lego"]   # the classification of pages has its own target (page_fuzzer.py)
URLS = ["https://a.example/", "https://b.example/shop/", "http://c.example/forum?id=3"]
STATUSES = ["finished", "failed", "in-progress", "offline"]
SOURCES = [None, "internal", "network", "target"]
VERDICTS = {"alive", "down", "tls", "unchecked"}
CODE_SPAN = re.compile(r"`[^`\n]*`")
DAY = dt.date(2026, 11, 25)


def text(fdp, most):
    return fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, most))


def result(fdp):
    """One probe's answer, as the API documents it (HTTP measurement)."""
    headers = {}
    for _ in range(fdp.ConsumeIntInRange(0, 3)):
        name = "location" if fdp.ConsumeBool() else text(fdp, 12)
        headers[name] = [text(fdp, 80) for _ in range(fdp.ConsumeIntInRange(1, 3))] if fdp.ConsumeBool() else text(fdp, 120)
    r = {"status": STATUSES[fdp.ConsumeIntInRange(0, 3)],
         "statusCode": fdp.ConsumeIntInRange(100, 599) if fdp.ConsumeBool() else None,
         "rawOutput": text(fdp, 200), "rawBody": text(fdp, 400) if fdp.ConsumeBool() else None, "headers": headers}
    source = SOURCES[fdp.ConsumeIntInRange(0, 3)]
    if source:
        r["failureSource"] = source
    return {"result": r}


class Api:
    """The Globalping API: its limits, a measurement created, then read; the answers come from the fuzzer."""

    def __init__(self, fdp):
        self.fdp, self.made = fdp, 0

    def __call__(self, path, body=None, token=None):
        fdp = self.fdp
        if path == "/limits":
            return {"rateLimit": {"measurements": {"create": {"remaining": fdp.ConsumeIntInRange(0, 60)}}}}
        if path == "/measurements":
            if fdp.ConsumeIntInRange(0, 9) == 0:
                raise urllib.error.HTTPError(path, 422, "no suitable probes", None, None)
            self.made += 1
            return {"id": str(self.made)}
        if fdp.ConsumeIntInRange(0, 15) == 0:
            return {"status": "in-progress", "results": []}
        return {"status": "finished", "results": [result(fdp) for _ in range(fdp.ConsumeIntInRange(0, 3))]}


def TestOneInput(data):
    fdp = atheris.FuzzedDataProvider(data)
    urls = URLS[: fdp.ConsumeIntInRange(1, len(URLS))]
    rechecked = links_issue.recheck(urls, api=Api(fdp), sleep=lambda _s: None)
    for u, (verdict, readings, extra) in rechecked.items():
        if u not in urls or verdict not in VERDICTS or not all(isinstance(x, str) for x in readings):
            raise AssertionError(f"recheck gave {u!r}: {verdict!r}, {readings!r}")
        if extra is not None and verdict != "alive":
            raise AssertionError(f"recheck gave a dead page for {u!r} judged {verdict!r}")
    why = text(fdp, 100).replace("\n", " ")   # lychee's reason quotes the server
    report = "### Errors in data/clubs.toml\n\n" + "".join(f"* [ERROR] <{u}> (at {i + 3}:8) | {why}\n" for i, u in enumerate(urls))
    body, _ = links_issue.body(report, rechecked=rechecked, today=DAY)
    bare = CODE_SPAN.sub("", body)
    for u in urls:
        bare = bare.replace(f"<{u}>", "")
    # the fixed sentences of links_issue.body hold no "@", "<http" or "`" today: one added there would fail this check every week
    if "@" in bare or "<http" in bare or "`" in bare:
        raise AssertionError("the issue quotes third-party text outside a code span:\n" + bare)


if __name__ == "__main__":
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()
