#!/usr/bin/env python3
"""Fuzz target: the answers of a third-party server to Data fixes (scripts/autofix.py, moved).

Data fixes follows the permanent redirects of every entry and writes the new address in data/*.toml. Here the
network is replaced by the answers of the fuzzer, read by the real http.client and urllib of Python: the status
line, the headers and the Location address are the server's. moved is called out of any try (main, through
ThreadPoolExecutor.map): it may not raise. It gives None or an address that the data file and the pull request
can hold: http or https, a host, no query, and a TOML string that reads back the same. Also counted: a run over
the time limit, memory.

Run by hand: python3 fuzz/redirect_fuzzer.py -dict=fuzz/redirect.dict -max_total_time=60
"""
import io
import pathlib
import re
import sys
import tomllib

import atheris

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
with atheris.instrument_imports():   # http.client and urllib too: they read the answer of the server
    import http.client  # noqa: E402
    import urllib.parse  # noqa: E402
    import urllib.request  # noqa: E402
    import autofix  # noqa: E402

STARTS = ["https://club.example/news/", "http://shop.example/fr/sets", "https://www.brand.example/"]
CODES = [200, 301, 308, 302, 307, 404, 500]
ANSWERS = []   # raw answers of the server, one per request
RESOLVABLE = re.compile(rb"[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?|[0-9A-Fa-f:.]+")   # host names and addresses (http.client strips the brackets)


class Socket:
    """What http.client reads and writes: the request goes nowhere, the answer is the fuzzer's."""

    def __init__(self, answer):
        self.answer = answer

    def sendall(self, _data):
        pass

    def makefile(self, *_args, **_kwargs):
        return io.BytesIO(self.answer)

    def close(self):
        pass


class Connection(http.client.HTTPConnection):
    def connect(self):
        if not RESOLVABLE.fullmatch(self.host.encode("idna")):   # as socket.create_connection: idna, then a name or an address
            raise OSError(f"name not resolved: {self.host!r}")
        self.sock = Socket(ANSWERS.pop(0) if ANSWERS else b"")


class Network(urllib.request.HTTPHandler, urllib.request.HTTPSHandler):
    """urllib's own handling of http and https, over Connection."""

    def http_open(self, req):
        return self.do_open(Connection, req)

    https_open = http_open
    https_request = urllib.request.HTTPHandler.http_request


autofix.OPENER = urllib.request.build_opener(autofix.NoRedirect, Network, urllib.request.ProxyHandler({}))   # no proxy, as on GitHub


def answer(fdp):
    """One answer: mostly a status line and a Location of the fuzzer, sometimes raw bytes."""
    if fdp.ConsumeIntInRange(0, 7) == 0:
        return fdp.ConsumeBytes(fdp.ConsumeIntInRange(0, 600))
    code = CODES[fdp.ConsumeIntInRange(0, len(CODES) - 1)] if fdp.ConsumeBool() else fdp.ConsumeIntInRange(100, 999)
    location = fdp.ConsumeBytes(fdp.ConsumeIntInRange(0, 300))
    return b"HTTP/1.1 %d X\r\nLocation: %s\r\nContent-Length: 0\r\n\r\n" % (code, location)


def TestOneInput(data):
    fdp = atheris.FuzzedDataProvider(data)
    start = STARTS[fdp.ConsumeIntInRange(0, len(STARTS) - 1)]
    ANSWERS[:] = [answer(fdp) for _ in range(fdp.ConsumeIntInRange(1, 6))]
    new = autofix.moved(start)
    if new is None:
        return
    if not isinstance(new, str) or not new.startswith(("http://", "https://")) or "?" in new:
        raise AssertionError(f"moved gave {new!r}")
    if not urllib.parse.urlsplit(new).hostname:
        raise AssertionError(f"moved gave {new!r}, an address without a host (main reads its host)")
    try:
        back = tomllib.loads(f'url = "{new}"\n')["url"]
    except tomllib.TOMLDecodeError:
        raise AssertionError(f"moved gave {new!r}, which breaks the data file") from None
    if back != new:
        raise AssertionError(f"moved gave {new!r}, read back from the data file as {back!r}")


if __name__ == "__main__":
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()
