#!/usr/bin/env python3
"""The image shown when a page of the website is shared (og:image): media/social.png, 1200 x 630.

Drawn from what the website itself says: its title, its English tagline and the host of PAGES (scripts/build.py), with
the logo and the font of the website (Nunito). The PNG carries what it shows (text chunk `shows`): `scripts/build.py
--check` fails when the title, the tagline or the address change and the image was not drawn again.

Usage: python3 scripts/social_image.py [--chrome /path/to/chrome]
Needs `pip install playwright pillow` and `playwright install chromium` (or --chrome).
"""
import argparse
import base64
import html
import io

from PIL import Image, PngImagePlugin
from playwright.sync_api import sync_playwright

import build

OUT = build.ROOT / "media" / "social.png"


def page():
    b64 = lambda p: base64.b64encode((build.ROOT / p).read_bytes()).decode()
    esc = html.escape
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:Nunito;src:url(data:font/woff2;base64,{b64("media/fonts/nunito.woff2")}) format("woff2");font-weight:200 1000}}
html,body{{margin:0}}
#c{{width:1200px;height:630px;box-sizing:border-box;padding:0 90px 0 100px;display:flex;align-items:center;gap:70px;font-family:Nunito,sans-serif;
background:#0b1a2e;background-image:linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px);background-size:30px 30px}}
#c img{{width:240px;flex:none}}
h1{{margin:0 0 22px;font-size:84px;line-height:1;font-weight:900;color:#eef4ff;letter-spacing:-1px}}
p{{margin:0;font-size:33px;line-height:1.3;color:#a9bcd6}}
.u{{margin-top:30px;font-size:27px;color:#f2c14e;font-weight:700}}
</style></head><body><div id="c"><img src="data:image/svg+xml;base64,{b64("media/logo.svg")}" alt="">
<div><h1>{esc(build.T["title"]["en"])}</h1><p>{esc(build.T["site_tagline"]["en"])}</p>
<p class="u">{esc(build.social_host())} · English · Français</p></div></div></body></html>'''


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--chrome")
    a = ap.parse_args()
    with sync_playwright() as p:
        browser = p.chromium.launch(**({"executable_path": a.chrome} if a.chrome else {}))
        pg = browser.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=1)
        pg.set_content(page())
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(300)
        png = pg.locator("#c").screenshot()
        browser.close()
    info = PngImagePlugin.PngInfo()
    info.add_text("shows", build.social_shows())
    Image.open(io.BytesIO(png)).save(OUT, pnginfo=info, optimize=True)
    print(f"✓ {OUT.relative_to(build.ROOT)} ({build.social_shows()})")


if __name__ == "__main__":
    main()
