#!/usr/bin/env python3
"""The image of the website at the top of the README: media/site-preview.png (light) and media/site-preview-dark.png.

The header of the website above two blocks side by side, "Where to start" and "Map of the brick world", fading at
the bottom; captured from the built site (site/) in English, en-GB, in both themes. Each PNG carries the version
it shows (text chunk `version`): `scripts/build.py --check` warns when it differs from VERSION, so a pull request
that raises the version takes the image again.

Usage: python3 scripts/build.py --site-only && python3 scripts/readme_image.py [--site site] [--chrome /path/to/chrome]
Needs `pip install playwright pillow` and `playwright install chromium` (or --chrome).
"""
import argparse
import base64
import functools
import http.server
import io
import threading
from pathlib import Path

from PIL import Image, PngImagePlugin
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = {"light": ROOT / "media" / "site-preview.png", "dark": ROOT / "media" / "site-preview-dark.png"}
COLUMN = 760      # width of the browser for each block: narrow enough for the cards to stay readable at README width
HEIGHT = 640      # height of each block, from its heading
PANEL = 430       # width of each block in the image (CSS pixels; the image is twice as large)
SCALE = 2


def capture(browser, base, theme):
    def page(width, height):
        pg = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=SCALE,
                              color_scheme=theme, locale="en-GB", timezone_id="Europe/London")
        pg.add_init_script(f"try{{localStorage.setItem('lang','en');localStorage.setItem('theme','{theme}')}}catch(e){{}}")
        pg.goto(base)
        pg.wait_for_function("document.querySelector('#journeys') && document.querySelector('#mapgrid')")
        pg.wait_for_timeout(800)  # fonts and the studs of the map
        return pg

    b64 = lambda png: base64.b64encode(png).decode()
    wide = page(1280, 900)
    header = wide.locator("header").first.bounding_box()
    head = b64(wide.screenshot(clip={"x": 0, "y": 0, "width": 1280, "height": header["height"]}))
    background = wide.evaluate("getComputedStyle(document.body).backgroundColor")
    version = wide.evaluate("(document.querySelector('header').innerText.match(/v(\\d+\\.\\d+)/)||[])[1]||''")
    narrow = page(COLUMN, 4000)
    narrow.evaluate("(document.getElementById('mapd')||{}).open=true")  # the map is folded by default
    blocks = []
    for sel in ("#start", "#map"):
        y = narrow.evaluate(f"document.querySelector('{sel}').getBoundingClientRect().top + scrollY")
        blocks.append(b64(narrow.screenshot(clip={"x": 0, "y": max(0, y - 12), "width": COLUMN, "height": HEIGHT}, full_page=True)))
    width = 2 * PANEL + 20
    panels = "".join(f'<img src="data:image/png;base64,{s}" style="width:{PANEL}px;display:block">' for s in blocks)
    comp = browser.new_page(viewport={"width": width + 40, "height": int(HEIGHT * PANEL / COLUMN) + 160}, device_scale_factor=SCALE)
    comp.set_content(f'''<html><body style="margin:0;background:transparent"><div id="c" style="padding:16px 20px 30px">
<div style="width:{width}px;border-radius:12px;overflow:hidden;background:{background};box-shadow:0 24px 60px -28px rgba(12,38,64,.45),0 0 0 1px rgba(12,38,64,.08);
-webkit-mask-image:linear-gradient(to bottom,#000 60%,transparent 100%)">
<img src="data:image/png;base64,{head}" style="width:{width}px;display:block">
<div style="display:flex;gap:20px;justify-content:center">{panels}</div></div></div></body></html>''')
    comp.wait_for_timeout(300)
    png = comp.locator("#c").screenshot(omit_background=True)
    for pg in (wide, narrow, comp):
        pg.close()
    return png, version


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--site", default=str(ROOT / "site"))
    ap.add_argument("--chrome")
    a = ap.parse_args()
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    handler = functools.partial(Quiet, directory=a.site)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    expected = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(**({"executable_path": a.chrome} if a.chrome else {}))
            for theme, out in OUT.items():
                png, version = capture(browser, f"http://127.0.0.1:{srv.server_address[1]}/", theme)
                if version != expected:
                    raise SystemExit(f"the site shows v{version or '?'}, VERSION is {expected}: run python3 scripts/build.py --site-only first")
                info = PngImagePlugin.PngInfo()
                info.add_text("version", version)
                Image.open(io.BytesIO(png)).save(out, pnginfo=info, optimize=True)
                print(f"✓ {out.relative_to(ROOT)} (v{version}, {theme})")
            browser.close()
    finally:
        srv.shutdown()


if __name__ == "__main__":
    main()
