#!/usr/bin/env python3
"""Rendering checks of the built website (site/), in a real browser (Playwright, Chromium).

Every view and state a visitor reaches (directory as cards and as a table, brand mode of an alternative brand and of LEGO, a search without result, observatory,
about page, hidden vault, page of an unknown address), in English and French, at several widths and in both
themes. Fails on:
- overflow: the page scrolls sideways, or an element sticks out of the box (card, panel, row) it sits in;
- broken token: a phone number, an email, a website, a date, a tag, a chip, a button label or a short
  part of an address split over two lines;
- broken word: a word split inside itself (not at a hyphen) when it fits on a line;
- overlapping text: two texts of a chart (SVG) drawn over one another (axis marks, labels);
- inherited frame: a list item framed or filled inside another framed list item (a rule meant for the
  outer rows reaching the inner ones);
- script error, console error, or content security policy violation;
- search: a word found only in the strengths or weaknesses of an entry (details.json, read after the page) must find it;
- the list drawn in parts (app.js, fillAll): every card drawn in the end; before that, printing, a link to one entry,
  a search typed at once and the change of language find every card where it should be (phone width, both languages);
- phones (640 px and less): the search bar on more than two lines, a field under 16 px (a phone zooms into it);
- dead CSS: a selector that matches nothing in any view and state checked, unless tests/css-states.txt names its
  state (not in --data-only runs);
- accessibility (axe-core, WCAG 2.2 A and AA rules: contrast on the real background, names of controls,
  target sizes, landmarks, ARIA): every violation, on the same views, at 1440 and 390 px in both themes. A guard,
  not a conformance target: the 13 px studs of the category map are accepted, and marks told apart by colour
  alone (WCAG 1.4.1) are not checked (decision of 24/11/2026).

Usage: python3 scripts/check_site.py [--site site] [--quick | --data-only] [--jobs N] [--chrome /path/to/chrome] [--axe path/to/axe.min.js]
Each width, theme and language opens in its own browser context; --jobs browsers (one per processor by default) take them in turn.
Needs `pip install playwright`, `playwright install chromium` (or --chrome) and `npm install axe-core`
(found in node_modules/ by default). Exit status 1 on any failure.
"""
import argparse
import functools
import http.server
import json
import re
import os
import queue
import tempfile
import socketserver
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Evaluated in the page; returns a list of [check, where, detail].
PROBE = r"""
({mobile, width}) => {
  const out = [], seen = new Set();
  const add = (k, el, d) => { const w = where(el), key = k + w + d; if (!seen.has(key)) { seen.add(key); out.push([k, w, d]) } };
  const where = el => { const c = el.closest('[id]'); return (c ? '#' + c.id + ' ' : '') + el.tagName.toLowerCase() + (el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\s+/).join('.') : '') };
  const txt = el => (el.innerText || el.textContent || el.getAttribute('aria-label') || '').trim().replace(/\s+/g, ' ').slice(0, 60);
  const vis = el => { if (!el.getClientRects().length) return false; const s = getComputedStyle(el); return s.visibility !== 'hidden' && +s.opacity !== 0 };
  const W = width;  // the device width: on a phone the layout viewport grows with the content instead of scrolling
  if (Math.max(document.documentElement.scrollWidth, innerWidth) > W + 1) add('overflow', document.documentElement, 'page scrolls sideways: ' + Math.max(document.documentElement.scrollWidth, innerWidth) + ' > ' + W);

  // the box an element sits in: nearest ancestor with a border or a background; a scrolling ancestor ends the search
  const boxOf = el => { for (let a = el.parentElement; a && a !== document.body; a = a.parentElement) { const s = getComputedStyle(a);
      if (/(auto|scroll|hidden)/.test(s.overflowX)) return null;
      if (parseFloat(s.borderLeftWidth) > 0 || parseFloat(s.borderRightWidth) > 0 || (s.backgroundColor !== 'rgba(0, 0, 0, 0)' && s.backgroundColor !== 'transparent')) return a }
    return null };
  const leaves = [...document.querySelectorAll('body *')].filter(el => !el.closest('svg') && vis(el) && [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()));
  for (const el of leaves) {
    const r = el.getBoundingClientRect();
    if (r.right > W + 1 && getComputedStyle(el).position !== 'fixed') { let s = false; for (let a = el.parentElement; a; a = a.parentElement) if (/(auto|scroll|hidden)/.test(getComputedStyle(a).overflowX)) { s = true; break } if (!s) add('overflow', el, 'beyond the window: ' + txt(el)) }
    const cs = getComputedStyle(el); if (cs.display !== 'inline' && cs.overflowX === 'visible' && el.scrollWidth > el.clientWidth + 1 && el.clientWidth > 0) add('overflow', el, 'text wider than its box: ' + txt(el));
    const b = boxOf(el); if (b) { const br = b.getBoundingClientRect(); if (r.right > br.right + 1 || r.left < br.left - 1) add('overflow', el, 'out of its box: ' + txt(el)) }
  }

  // tokens that must stay on one line: count the lines their text actually takes
  const lines = el => { const tops = []; const tw = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); const rg = document.createRange(); let n;
    while ((n = tw.nextNode())) { if (!n.textContent.trim()) continue; rg.selectNodeContents(n); for (const q of rg.getClientRects()) if (q.width > 0.5) tops.push(q.top) }
    tops.sort((x, y) => x - y); let k = tops.length ? 1 : 0; for (let i = 1; i < tops.length; i++) if (tops[i] - tops[i - 1] > 6) k++; return k };
  const ATOM = '.ct .tel a, .ct .mail a, .ct .nw, time, .tag:not(.langs), .chip, .btn:not(.all), .kpi b, .pill';  // a full-width button may take two lines
  for (const el of document.querySelectorAll(ATOM)) if (vis(el) && lines(el) > 1) add('broken token', el, txt(el));

  // words split inside themselves (not at a hyphen or a slash) although they fit on a line; Chinese, Japanese and Korean
  // text breaks between any two characters, so it is not a word here
  const rg = document.createRange();
  for (const el of leaves) { const cw = el.getBoundingClientRect().width; for (const n of el.childNodes) { if (n.nodeType !== 3) continue; const t = n.textContent; const re = /[^\s\-\/‐-―\u3000-\u30ff\u3400-\u9fff\uac00-\ud7af\uff00-\uffef]{4,}/g; let m;
      while ((m = re.exec(t))) { rg.setStart(n, m.index); rg.setEnd(n, m.index + m[0].length); const rs = rg.getClientRects(); if (rs.length > 1) { const w = [...rs].reduce((a, x) => a + x.width, 0); if (w < cw - 2) add('broken word', el, m[0]) } } } }

  // a card's group label: beside the name, on its first line, never below it
  for (const h of document.querySelectorAll('.card .h')) { const a = h.querySelector('a'), g = h.querySelector('.g'); if (!a || !g || !vis(g)) continue;
    const ra = a.getBoundingClientRect(), r = document.createRange(); r.selectNodeContents(g); const ls = [...r.getClientRects()].filter(q => q.width > 0.5);
    const top = [...a.getClientRects()][0]; if (ls.length === 1 && top && ls[0].left >= top.right - 1 && ls[0].top < top.bottom) continue; add('misaligned label', g, txt(g)) }  // each text line, not the box

  // texts of a chart (SVG) drawn over one another: axis marks, labels
  for (const svg of document.querySelectorAll('svg')) { if (!vis(svg)) continue;
    const ts = [...svg.querySelectorAll('text')].filter(t => t.textContent.trim()).map(t => [t, t.getBBox()]);
    for (let i = 0; i < ts.length; i++) for (let j = i + 1; j < ts.length; j++) { const a = ts[i][1], b = ts[j][1];
      if (a.x < b.x + b.width - 1 && b.x < a.x + a.width - 1 && a.y < b.y + b.height - 1 && b.y < a.y + a.height - 1) add('overlapping text', ts[j][0], ts[i][0].textContent.trim() + ' / ' + ts[j][0].textContent.trim()) } }

  // a framed list item inside another framed list item
  const framed = el => { const s = getComputedStyle(el); return parseFloat(s.borderTopWidth) > 0 || (s.backgroundColor !== 'rgba(0, 0, 0, 0)' && s.backgroundColor !== 'transparent') };
  for (const li of document.querySelectorAll('li li')) if (vis(li) && framed(li)) { const o = li.parentElement.closest('li'); if (o && framed(o)) add('inherited frame', li, txt(li)) }

  return out
}
"""

# states: (name, path, script run before the probe)
# axe reads every node: the directory is narrowed to three categories (134 cards, the richest ones) to keep a run short
AXE_STATES = [
    ("directory", "#cat=places,events,clubs", "document.querySelectorAll('#list details').forEach(d=>d.open=true)"),
    ("bar folded, filters open", "#cat=shops", "scrollTo(0,document.getElementById('list').getBoundingClientRect().top+scrollY+400);setTimeout(()=>document.getElementById('ftoggle').click(),100)"),  # the stuck bar folds; its panel opens over the list
    ("lead-in", "", "(document.getElementById('mapd')||{}).open=true;document.getElementById('list').hidden=true"),  # "Where to start" and the map, shown when nothing is asked
    ("table", "#cat=places,events,clubs&view=table", ""),
    ("brand mode", "#q=COBI", ""),
    ("brand mode of LEGO", "#q=LEGO", ""),
    ("no result", "#q=qqzzxxkw", ""),  # a search that finds nothing: the drawing and the way to suggest a resource
    ("observatory", "#observatory", ""),
    ("observatory after a theme switch", "#observatory",  # colours computed by the page must follow the theme button
     "(()=>{const want=matchMedia('(prefers-color-scheme: dark)').matches?'light':'dark',tb=document.getElementById('theme');for(let i=0;i<3&&document.documentElement.dataset.theme!==want;i++)tb.click()})()"),
]
STATES = [
    ("directory", "", "(document.getElementById('mapd')||{}).open=true;document.querySelectorAll('#list details').forEach(d=>d.open=true)"),
    ("table", "#view=table", ""),
    ("bar folded, filters open", "#cat=shops", "scrollTo(0,document.getElementById('list').getBoundingClientRect().top+scrollY+400);setTimeout(()=>document.getElementById('ftoggle').click(),100)"),  # the stuck bar folds; its panel opens over the list
    ("brand mode", "#q=COBI", ""),
    ("brand mode of LEGO", "#q=LEGO", ""),
    ("no result", "#q=qqzzxxkw", ""),
    ("observatory", "#observatory", ""),
]


# the results of a search hold this entry (the whole directory, shown before the search, holds every entry: it is not a result)
FOUND = "id => !!document.querySelector('#list .rk') && !!document.getElementById('r-' + id)"
FILLED = "() => !document.querySelector('#list [data-ph]')"  # every card of the list drawn (app.js draws the first ones at once, the others when the browser is idle)

# CSS of a selector that matches nothing in any view and state checked here: dead, unless tests/css-states.txt names the state it is for
CSS_SELECTORS = r"""()=>{const out=[],err=[];const dyn=/::?(hover|focus-visible|focus-within|focus|active|visited|link|target|placeholder|before|after|marker|selection|backdrop|first-letter|first-line|-webkit-[a-z-]+|-moz-[a-z-]+)(\([^)]*\))?/g;
const walk=rules=>{for(const r of rules){if(r.cssRules&&!r.selectorText)walk(r.cssRules);else if(r.selectorText){for(const s of r.selectorText.split(/,(?![^(]*\))/)){const t=s.replace(dyn,'').trim()||'*';let m=true;try{m=!!document.querySelector(t)}catch(e){m=true}out.push([s.trim(),m])}}}};
for(const sh of document.styleSheets){try{walk(sh.cssRules)}catch(e){err.push(sh.href||'inline style')}}return {sel:out,err}}"""

# phones: the search bar on two lines at most (search line, then one row of controls), fields at 16 px or more (a phone zooms into a smaller one)
PHONE = r"""(w)=>{const out=[],row=document.querySelector('.bar .row');
if(!row)out.push(['phone check','.bar .row','no search bar found: the bar check sees nothing']);else{const rs=[...row.children].filter(e=>e.offsetParent&&getComputedStyle(e).display!=='none').map(e=>e.getBoundingClientRect()).sort((x,y)=>x.top-y.top);let n=0,low=-1e9;for(const r of rs){if(r.top>=low-2)n++;low=Math.max(low,r.bottom)}if(n>2)out.push(['bar on more than two lines','.bar .row',n+' lines, the search field included'])}
for(const e of document.querySelectorAll('input:not([type=checkbox]):not([type=radio]),select,textarea')){if(!e.offsetParent)continue;const f=parseFloat(getComputedStyle(e).fontSize);if(f<16)out.push(['field under 16 px',(e.id?'#'+e.id:e.tagName.toLowerCase()),f+' px: a phone zooms into it'])}
return out}"""


def details_word(site, lang):
    """A word of the strengths or weaknesses of one entry that no other text of the directory holds."""
    import re
    import unicodedata
    fold = lambda x: unicodedata.normalize("NFD", x.lower()).encode("ascii", "ignore").decode()
    data = json.loads((site / "data.json").read_text(encoding="utf-8"))  # every text, as scripts/build.py wrote it
    det = {r["id"]: (r[lang]["strengths"], r[lang]["weaknesses"]) for r in data["resources"]}
    other = fold(" ".join(" ".join([r["name"], r[lang]["summary"], r[lang]["group"], str(r[lang].get("size", "")), str(r.get("city") or "")]) for r in data["resources"]))
    words = {}
    for rid, (st, wk) in det.items():
        for w in set(re.findall(r"[a-zà-ÿ]{7,}", fold(" ".join(st + wk)))):
            words.setdefault(w, set()).add(rid)
    for w, ids in sorted(words.items()):
        if len(ids) == 1 and w not in other:
            return w, next(iter(ids))
    raise SystemExit("no word found only in the strengths and weaknesses")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default=str(ROOT / "site"))
    ap.add_argument("--quick", action="store_true", help="one width per class (1440, 390) and the light theme only for layout")
    ap.add_argument("--chrome", default="", help="Chrome or Chromium to use instead of Playwright's")
    ap.add_argument("--json", default="", help="write the findings to this file")
    ap.add_argument("--no-axe", action="store_true", help="layout checks only")
    ap.add_argument("--data-only", action="store_true", help="for a change of data alone (workflow Render): layout at 1440, 390 and 320 px in the light theme, "
                    "no accessibility pass; colours, controls and landmarks come from the source of the website, not from the data")
    ap.add_argument("--dejavu", action="store_true", help="draw system-ui and sans-serif with DejaVu Sans, as on the Ubuntu runners of GitHub Actions (wider than most desktop fonts)")
    ap.add_argument("--axe", default=str(ROOT / "node_modules" / "axe-core" / "axe.min.js"), help="axe-core build (npm install axe-core)")
    ap.add_argument("--jobs", type=int, default=min(8, getattr(os, "process_cpu_count", os.cpu_count)() or 1), help="browsers run side by side (default: one per processor, 8 at most)")
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *x):
            pass

        def handle(self):
            try:
                super().handle()
            except (BrokenPipeError, ConnectionResetError):
                pass  # the browser closed a page while a file was being sent
    h = functools.partial(Quiet, directory=a.site)
    class Server(socketserver.ThreadingTCPServer):
        request_queue_size = 128  # several browsers open their connections at once
    srv = Server(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}/"
    widths = [1440, 390, 320] if a.data_only else [1440, 390] if a.quick else [1440, 1024, 768, 390, 320]
    found = {}
    lock = threading.Lock()

    def record(where, items):
        with lock:
            for k, at, detail in items:
                found.setdefault((k, at, detail), []).append(where)

    env = dict(os.environ)
    if a.dejavu:
        conf = Path(tempfile.mkdtemp()) / "fonts.conf"
        conf.write_text('<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig><include ignore_missing="yes">/etc/fonts/fonts.conf</include>'
                        + "".join(f'<alias binding="strong"><family>{f}</family><prefer><family>{t}</family></prefer></alias>' for f, t in
                                  (("system-ui", "DejaVu Sans"), ("sans-serif", "DejaVu Sans"), ("monospace", "DejaVu Sans Mono"))) + "</fontconfig>")
        env["FONTCONFIG_FILE"] = str(conf)

    def launch(p):
        return p.chromium.launch(**({"executable_path": a.chrome} if a.chrome else {}), args=["--no-sandbox"], env=env)

    with sync_playwright() as p:
        b = launch(p)
        # calibration: the probe must find exactly the defects planted in tests/render-fixture.html
        pg = b.new_page(viewport={"width": 390, "height": 900})
        pg.set_content((ROOT / "tests" / "render-fixture.html").read_text(encoding="utf-8"))
        got = {(k, d) for k, w, d in pg.evaluate(PROBE, {"mobile": True, "width": 390})}
        want = {tuple(x) for x in pg.evaluate("[...document.querySelectorAll('[data-expect]')].map(e=>[e.dataset.expect,(e.innerText||'').trim().replace(/\\s+/g,' ').slice(0,60)])")}
        def hit(k, d):
            return any(k == gk and (gd.split(': ')[-1][:20] in d or d[:20] in gd) for gk, gd in got)
        missed = [f"{k}: {d}" for k, d in want if not hit(k, d)]
        extra = [f"{k}: {d}" for k, d in got if not any(k == wk and (d.split(': ')[-1][:20] in wd or wd[:20] in d) for wk, wd in want)]
        # the phone and dead-CSS checks on tests/phone-fixture.html: exactly the three defects it plants
        pg.set_content((ROOT / "tests" / "phone-fixture.html").read_text(encoding="utf-8"))
        phone = {(k, where) for k, where, _ in pg.evaluate(PHONE, 390)}
        css = pg.evaluate(CSS_SELECTORS)
        dead = {x for x, m in css["sel"] if not m}
        planted = {("bar on more than two lines", ".bar .row"), ("field under 16 px", "#tiny")}
        missed += [f"{k}: {w}" for k, w in planted - phone] + ([] if ".dead-rule" in dead else ["CSS matching nothing: .dead-rule"])
        extra += [f"{k}: {w}" for k, w in phone - planted] + [f"CSS matching nothing: {x}" for x in dead - {".dead-rule"}] + css["err"]
        b.close()
    if missed or extra:
        print("✗ calibration of the checks failed (tests/render-fixture.html, tests/phone-fixture.html)")
        for m in missed:
            print("   not found:", m)
        for x in extra:
            print("   unexpected:", x)
        return 1
    print(f"✓ calibration: {len(want) + len(planted) + 1} planted defects found, nothing else")

    css_seen, css_used = set(), set()

    def selectors(pg):
        if a.data_only:
            return
        got = pg.evaluate(CSS_SELECTORS)
        record("css", [("CSS check", h, "stylesheet unreadable: the dead-CSS check cannot see its rules") for h in got["err"]])
        with lock:
            css_seen.update(x for x, _ in got["sel"])
            css_used.update(x for x, m in got["sel"] if m)

    def filled(pg, where):
        try:
            pg.wait_for_function(FILLED, timeout=20000)
        except PlaywrightTimeout:
            record(where, [("list in parts", "#list", "empty cards left 20 s after the page")])

    # each job opens its own browser context and records what it finds; the jobs run side by side (--jobs browsers)
    def layout(b, lang, root, w, theme):
        mobile = w < 700
        c = b.new_context(viewport={"width": w, "height": 900}, locale="fr-FR" if lang == "fr" else "en-GB",
                          color_scheme=theme, is_mobile=mobile, has_touch=mobile, device_scale_factor=2 if mobile else 1)
        c.add_init_script("addEventListener('securitypolicyviolation',e=>console.error('CSP '+e.violatedDirective+' '+e.blockedURI))")
        pg = c.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        for name, frag, js in STATES:
            pg.goto(base + root + frag)
            pg.reload()
            pg.wait_for_selector("html.ready", state="attached")
            filled(pg, f"{lang} {w} {theme} {name}")  # the cards drawn after the first ones, while the browser is idle
            pg.wait_for_timeout(300)
            pg.add_style_tag(content="*{content-visibility:visible!important}")  # every card laid out, so that every card is checked
            if js:
                pg.evaluate(js)
                pg.wait_for_timeout(400)
            record(f"{lang} {w} {theme} {name}", pg.evaluate(PROBE, {"mobile": mobile, "width": w}))
            if name == "directory" and w <= 640:
                record(f"{lang} {w} {theme} {name}", pg.evaluate(PHONE, w))
            selectors(pg)
        pg.goto(base + root + "about/")  # the about page of the language: shared header, its own layout
        pg.wait_for_timeout(300)
        record(f"{lang} {w} {theme} about", pg.evaluate(PROBE, {"mobile": mobile, "width": w}))
        selectors(pg)
        if lang == "en":
            pg.goto(base + "vault/")
            pg.wait_for_timeout(700)
            record(f"{lang} {w} {theme} vault", pg.evaluate(PROBE, {"mobile": mobile, "width": w}))
            selectors(pg)
            pg.goto(base + "404.html")  # the page GitHub Pages serves for an unknown address, in both languages
            pg.wait_for_timeout(300)
            record(f"{lang} {w} {theme} not found", pg.evaluate(PROBE, {"mobile": mobile, "width": w}))
            selectors(pg)
        record(f"{lang} {w} {theme}", [("script error", "", e[:160]) for e in errs])
        c.close()

    def search(b, lang, root, word, rid):
        # strengths and weaknesses come from details.json, read after the page; a word found only there must still find its entry
        c = b.new_context(viewport={"width": 1440, "height": 900}, locale="fr-FR" if lang == "fr" else "en-GB")
        pg = c.new_page()
        pg.goto(base + root)
        pg.wait_for_selector("html.ready", state="attached")
        pg.fill("#q", word)
        try:  # details.json read, index rebuilt, results drawn
            pg.wait_for_function(FOUND, arg=rid, timeout=10000)
        except PlaywrightTimeout:
            record(lang, [("search", "#q", f"'{word}', only in the strengths or weaknesses of {rid}, does not find it")])
        c.close()

    def parts(b, lang, root, last, mid):
        # the list is drawn in parts: the first cards at once, the others while the browser is idle (empty cards until then, data-ph);
        # what needs every card where it will be fills them all first. Checked in a browser that is never idle (requestIdleCallback
        # never calls back), so that only the cards near the screen and those filled on purpose are drawn; then in a normal one.
        where = f"{lang} 390 light list in parts"
        errs, out = [], []
        c = b.new_context(viewport={"width": 390, "height": 844}, locale="fr-FR" if lang == "fr" else "en-GB", is_mobile=True, has_touch=True, device_scale_factor=2)
        pg = c.new_page()
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(base + root)
        pg.wait_for_selector("html.ready", state="attached")
        filled(pg, where)
        n = pg.evaluate("document.querySelectorAll('#list .card .h').length")
        if n != total:
            out.append(("list in parts", "#list", f"{n} cards drawn, {total} entries"))
        c.close()
        c = b.new_context(viewport={"width": 390, "height": 844}, locale="fr-FR" if lang == "fr" else "en-GB", is_mobile=True, has_touch=True, device_scale_factor=2)
        c.add_init_script("window.requestIdleCallback=()=>0")
        pg = c.new_page()
        pg.on("pageerror", lambda e: errs.append(str(e)))

        def load(frag=""):
            pg.goto(base + root + frag)
            pg.reload()
            pg.wait_for_selector("html.ready", state="attached")
        load()
        if pg.evaluate("document.querySelectorAll('#list [data-ph]').length") == 0:
            out.append(("list in parts", "#list", "every card drawn at once: the checks below see nothing"))
        if pg.evaluate("document.querySelectorAll('#list [data-ph]:not([aria-hidden=true])').length"):
            out.append(("list in parts", "#list", "an empty card is not hidden from screen readers (aria-hidden)"))
        if pg.evaluate("dispatchEvent(new Event('beforeprint')),document.querySelectorAll('#list [data-ph]').length"):
            out.append(("list in parts", "#list", "printing leaves empty cards"))
        load()
        pg.keyboard.press("Control+f")  # the search of the browser finds only what is drawn
        if pg.evaluate("document.querySelectorAll('#list [data-ph]').length"):
            out.append(("list in parts", "#list", "Ctrl+F leaves empty cards"))
        for rid in (last, mid):  # the last entry of the data, the first of a middle category: their cards are among the empty ones at first
            load(f"#entry={rid}")
            pg.wait_for_timeout(1500)
            got = pg.evaluate(f"(()=>{{const e=document.getElementById('r-{rid}');if(!e)return 'no card';if(!e.querySelector('.h'))return 'empty card';if(!e.classList.contains('focus'))return 'card not marked';"
                              "if([...document.querySelectorAll('#list [data-ph]')].some(p=>p.compareDocumentPosition(e)&Node.DOCUMENT_POSITION_FOLLOWING))return 'an empty card above it';"
                              f"const r=e.getBoundingClientRect();return r.top>=0&&r.top<innerHeight?'':'card out of view at '+Math.round(r.top)}})()")
            if got:
                out.append(("list in parts", f"#entry={rid}", got))
        load()
        pg.fill("#q", re.sub(r"[^\w ]+", " ", lastname).strip())  # the search typed at once: the index is not built yet
        try:
            pg.wait_for_function(FOUND, arg=last, timeout=10000)
        except PlaywrightTimeout:
            out.append(("list in parts", "#q", f"a search typed at once does not find {last}"))
        if lang == "en":  # the change of language keeps the element at the top of the view in place, although the other page draws it later
            load()
            pg.evaluate(f"document.getElementById('r-{last}').scrollIntoView({{block:'start'}})")
            pg.wait_for_timeout(300)
            pg.evaluate("document.getElementById('langbtn').addEventListener('click',e=>e.preventDefault(),{once:true})")  # after the page's own handler, which keeps the place
            pg.click("#langbtn")
            at = pg.evaluate("(()=>{try{return JSON.parse(sessionStorage.getItem('langpos'))}catch(e){return null}})()") or {}
            pg.goto(pg.evaluate("document.getElementById('langbtn').href"))
            pg.wait_for_selector("html[lang=fr].ready", state="attached")
            pg.wait_for_timeout(3000)
            top = pg.evaluate(f"(()=>{{const e=document.getElementById({json.dumps(at.get('id', ''))});return e&&e.offsetParent?Math.round(e.getBoundingClientRect().top):null}})()")
            if not at.get("id"):
                out.append(("list in parts", "#langbtn", "the change of language keeps no place"))
            elif top is None or abs(top - at["dy"]) > 4:
                out.append(("list in parts", "#langbtn", f"after the change of language, #{at['id']} moved from {at['dy']} to {top} px"))
        record(where, out + [("script error", "", e[:160]) for e in errs])
        c.close()

    def access(b, lang, root, w, theme):
        # accessibility: axe-core injected into the page (the page's own security policy is bypassed for that only)
        mobile = w < 700
        c = b.new_context(viewport={"width": w, "height": 900}, locale="fr-FR" if lang == "fr" else "en-GB", color_scheme=theme,
                          is_mobile=mobile, has_touch=mobile, bypass_csp=True)
        pg = c.new_page()
        for name, frag, js in AXE_STATES + [("about", "about/", "")] + ([("vault", "vault/", ""), ("not found", "404.html", "")] if lang == "en" else []):
            pg.goto(base + (frag if name in ("vault", "not found") else root + frag))
            if name not in ("vault", "about", "not found"):
                pg.reload()
                pg.wait_for_selector("html.ready", state="attached")
                filled(pg, f"{lang} {w} {theme} {name}")
            pg.wait_for_timeout(300)
            if js:
                pg.evaluate(js)
                pg.wait_for_timeout(400)
            pg.add_style_tag(content="*{content-visibility:visible!important}")
            pg.add_script_tag(path=str(axe))
            pg.evaluate("window.scrollTo(0,0)")  # a sticky header over a scrolled view would count as covering its targets
            res = pg.evaluate("""async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']},resultTypes:['violations']});
              return r.violations.flatMap(v=>v.nodes.map(n=>[v.id,n.target.join(' '),(n.failureSummary||'').split('\\n').slice(1,2).join('').trim().slice(0,120)]))}""")
            res = [x for x in res if not (x[0] == "target-size" and ".stud" in x[1])]  # accepted: 13 px studs (decision of 24/11/2026)
            record(f"{lang} {w} {theme} {name}", [["a11y " + k, t, d] for k, t, d in res])
        c.close()

    langs = (("en", ""), ("fr", "fr/"))
    jobs = []  # longest first, so that no long job starts last
    axe = Path(a.axe)
    if a.no_axe or a.data_only:
        pass
    elif not axe.exists():
        record("setup", [("accessibility", "", f"axe-core not found at {axe}: npm install axe-core")])
    else:
        jobs += [(access, lang, root, w, theme) for lang, root in langs for w in (1440, 390) for theme in ("light", "dark")]
    jobs += [(layout, lang, root, w, theme) for lang, root in langs for w in widths for theme in ("light", "dark")
             if not (theme == "dark" and (a.data_only or w not in (1440, 390)))]  # colours do not depend on the width; layout is checked in light
    jobs += [(search, lang, root, *details_word(Path(a.site), lang)) for lang, root in langs]  # in the main thread: its SystemExit must stop the run
    site_data = json.loads((Path(a.site) / "data.json").read_text(encoding="utf-8"))
    rows, cats = site_data["resources"], [c["id"] for c in site_data["categories"]]
    total, lastname = len(rows), rows[-1]["name"]
    mid = next(r["id"] for r in rows if r["cat"] == cats[len(cats) // 2])  # beyond the first cards, with categories below it
    jobs += [(parts, lang, root, rows[-1]["id"], mid) for lang, root in langs]
    todo = queue.Queue()
    for j in jobs:
        todo.put(j)
    errors = []

    def worker():
        # one Playwright and one browser per thread: the synchronous API of Playwright is not shared between threads
        try:
            with sync_playwright() as p:
                b = launch(p)
                while True:
                    try:
                        j = todo.get_nowait()
                    except queue.Empty:
                        break
                    j[0](b, *j[1:])
                b.close()
        except BaseException as e:  # noqa: BLE001 (raised again below, in the main thread; a thread swallows SystemExit)
            errors.append(e)
            while not todo.empty():  # the run fails: the other threads stop after their current job
                try:
                    todo.get_nowait()
                except queue.Empty:
                    break
    threads = [threading.Thread(target=worker) for _ in range(max(1, min(a.jobs, len(jobs))))]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    if errors:
        raise errors[0]
    srv.shutdown()
    if not a.data_only:
        known = {re.split(r"\s+#\s", l)[0].strip() for l in (ROOT / "tests" / "css-states.txt").read_text(encoding="utf-8").splitlines()
                 if l.strip() and not l.startswith("# ")}  # "selector   # state"; a line starting "# " is a comment
        record("css", [("CSS matching nothing", x, "in no view or state checked: remove it, or name its state in tests/css-states.txt")
                       for x in sorted(css_seen - css_used - known)])
        record("css", [("CSS states list", x, "names a selector that no longer exists: remove it from tests/css-states.txt")
                       for x in sorted(known - css_seen)])
        if not css_seen:
            record("css", [("CSS check", "", "no CSS rule read in any view: the dead-CSS check sees nothing")])

    states = [n for n, _, _ in STATES + AXE_STATES] + ["about", "vault", "list in parts"]

    def order(where):  # "en 1440 light directory": language, widest first, light first, states in their order
        t = where.split(" ")
        w = int(t[1]) if len(t) > 1 and t[1].isdigit() else 0
        st = " ".join(t[3:])
        return (t[0], -w, t[2] != "light" if len(t) > 2 else False, states.index(st) if st in states else -1, where)

    by = {}
    for (k, where, detail), ctx in found.items():
        by.setdefault(k, []).append((where, detail, sorted(ctx, key=order)))
    for v in by.values():
        v.sort(key=lambda x: (order(x[2][0]), x[0], x[1]))  # the jobs end in any order: findings and their contexts in the order of the checks
    if a.json:
        Path(a.json).write_text(json.dumps({k: [{"where": w, "detail": d, "seen": c} for w, d, c in v] for k, v in by.items()}, ensure_ascii=False, indent=1))
    for k, v in sorted(by.items()):
        print(f"✗ {k}: {len(v)}")
        for where, detail, ctx in v[:12]:
            print(f"   {where} — {detail}  [{ctx[0]}{' +' + str(len(ctx) - 1) if len(ctx) > 1 else ''}]")
        if len(v) > 12:
            print(f"   … {len(v) - 12} more")
    if not by:
        print(f"✓ rendering: {len(widths)} widths, {'1 theme' if a.data_only else '2 themes'}, 2 languages, {len(STATES) + 1} views" + (" (data only: no accessibility pass)" if a.data_only else ""))
    return 1 if by else 0


if __name__ == "__main__":
    sys.exit(main())
