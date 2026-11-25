#!/usr/bin/env python3
"""Speed of the built website (site/) on a slow phone: the time until the directory's list is displayed.

A step that changes how the page is built is kept only if it lowers this time by 10 % at least on the slower of the
two pages (decision of 24/11/2026, 10:40). Conditions: Chromium, processor slowed 4 times, slow 4G network (150 ms
round trip, 1.6 Mbit/s down, 750 kbit/s up), files compressed with gzip as GitHub Pages sends them, empty cache, a 390 px wide phone; each page loaded 5 times, the median
kept. Measured on every load:
- list: from the start of the navigation to the first frame painted after the list holds its cards;
- longest task and total blocking time (the part of each task beyond 50 ms) until then, for information.

Usage: python3 scripts/measure_speed.py [--site site] [--runs 5] [--json out.json] [--chrome /path/to/chrome]
Needs `pip install playwright` and `playwright install chromium` (or --chrome). Prints one line per page.
"""
import argparse
import functools
import gzip
import http.server
import json
import socketserver
import statistics
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

WATCH = """
window.__speed = {tasks: []};
new PerformanceObserver(l => { for (const e of l.getEntries()) window.__speed.tasks.push([e.startTime, e.duration]) }).observe({type: 'longtask', buffered: true});
const mo = new MutationObserver(() => {
  if (window.__speed.list) return;
  const list = document.getElementById('list');
  if (list && list.querySelector('.card')) {
    window.__speed.list = -1;
    requestAnimationFrame(() => requestAnimationFrame(() => { window.__speed.list = performance.now() }));
  }
});
mo.observe(document, {childList: true, subtree: true});  // from the first byte: the page's script fills the list before DOMContentLoaded
"""


def measure(browser, url):
    c = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2,
                            bypass_csp=True)  # the page's policy would refuse the measuring script
    c.add_init_script(WATCH)
    pg = c.new_page()
    cdp = c.new_cdp_session(pg)
    cdp.send("Network.enable")
    cdp.send("Network.setCacheDisabled", {"cacheDisabled": True})
    cdp.send("Network.emulateNetworkConditions", {"offline": False, "latency": 150, "downloadThroughput": 1.6e6 / 8, "uploadThroughput": 750e3 / 8})
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
    pg.goto(url, wait_until="load", timeout=120000)
    pg.wait_for_function("window.__speed && window.__speed.list > 0", timeout=120000)
    pg.wait_for_timeout(300)
    s = pg.evaluate("window.__speed")
    c.close()
    before = [(t, d) for t, d in s["tasks"] if t < s["list"]]
    return {"list": round(s["list"]), "longest": round(max((d for _, d in before), default=0)), "blocking": round(sum(max(0, d - 50) for _, d in before))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default=str(ROOT / "site"))
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--json", default="")
    ap.add_argument("--chrome", default="")
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright

    class Gzip(http.server.SimpleHTTPRequestHandler):
        """Compressed like GitHub Pages serves text files (gzip), so that the bytes on the wire are the real ones."""
        def log_message(self, *x):
            pass

        def do_GET(self):
            path = Path(self.translate_path(self.path))
            if path.is_dir():
                path = path / "index.html"
            if not path.is_file():
                return super().do_GET()
            body = path.read_bytes()
            kind = self.guess_type(str(path))
            zipped = "gzip" in self.headers.get("Accept-Encoding", "") and kind.split("/")[0] in ("text", "application") and not kind.endswith(("png", "woff2"))
            if zipped:
                body = gzip.compress(body, 6)
            self.send_response(200)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            if zipped:
                self.send_header("Content-Encoding", "gzip")
            self.end_headers()
            self.wfile.write(body)
    Quiet = Gzip
    srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=a.site))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}/"
    out = {}
    with sync_playwright() as p:
        b = p.chromium.launch(**({"executable_path": a.chrome} if a.chrome else {}), args=["--no-sandbox"])
        for name, path in (("en", ""), ("fr", "fr/")):
            runs = [measure(b, base + path) for _ in range(a.runs)]
            med = {k: statistics.median(r[k] for r in runs) for k in runs[0]}
            out[name] = {"median": med, "runs": runs}
            print(f"{name}: list {med['list']:.0f} ms, longest task {med['longest']:.0f} ms, blocking {med['blocking']:.0f} ms  (runs: {', '.join(str(r['list']) for r in runs)})")
        b.close()
    srv.shutdown()
    worst = max(out[k]["median"]["list"] for k in out)
    print(f"slower page: {worst:.0f} ms")
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
