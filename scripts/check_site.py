#!/usr/bin/env python3
"""Rendering checks of the built website (site/), in a real browser (Playwright, Chromium).

Every view and state a visitor reaches (directory as cards and as a table, brand mode of an alternative brand and of LEGO, observatory,
hidden vault), in English and French, at several widths and in both
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
    ("observatory", "#observatory", ""),
]


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
        b.close()
    if missed or extra:
        print("✗ calibration of the checks failed (tests/render-fixture.html)")
        for m in missed:
            print("   not found:", m)
        for x in extra:
            print("   unexpected:", x)
        return 1
    print(f"✓ calibration: {len(want)} planted defects found, nothing else")

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
            pg.wait_for_timeout(300)
            pg.add_style_tag(content="*{content-visibility:visible!important}")  # every card laid out, so that every card is checked
            if js:
                pg.evaluate(js)
                pg.wait_for_timeout(400)
            record(f"{lang} {w} {theme} {name}", pg.evaluate(PROBE, {"mobile": mobile, "width": w}))
        if lang == "en":
            pg.goto(base + "vault/")
            pg.wait_for_timeout(700)
            record(f"{lang} {w} {theme} vault", pg.evaluate(PROBE, {"mobile": mobile, "width": w}))
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
            pg.wait_for_selector(f"#list #r-{rid}", state="attached", timeout=10000)
        except PlaywrightTimeout:
            record(lang, [("search", "#q", f"'{word}', only in the strengths or weaknesses of {rid}, does not find it")])
        c.close()

    def access(b, lang, root, w, theme):
        # accessibility: axe-core injected into the page (the page's own security policy is bypassed for that only)
        mobile = w < 700
        c = b.new_context(viewport={"width": w, "height": 900}, locale="fr-FR" if lang == "fr" else "en-GB", color_scheme=theme,
                          is_mobile=mobile, has_touch=mobile, bypass_csp=True)
        pg = c.new_page()
        for name, frag, js in AXE_STATES + ([("vault", "vault/", "")] if lang == "en" else []):
            pg.goto(base + (frag if name == "vault" else root + frag))
            if name != "vault":
                pg.reload()
                pg.wait_for_selector("html.ready", state="attached")
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

    states = [n for n, _, _ in STATES + AXE_STATES] + ["vault"]

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
