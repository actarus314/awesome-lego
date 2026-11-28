"""Tests of scripts/build.py: the validation refuses what data/SCHEMA.md forbids, and the pages keep their
invariants (every placeholder replaced, every inline script allowed by the security policy, texts present at
first paint). Standard library only: python3 -m unittest discover -s tests"""
import contextlib
import hashlib
import base64
import io
import json
import re
import shutil
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build  # noqa: E402


def load_with(file, edit):
    """Run build.load() on a copy of data/ where `edit(text)` changed one file; return its errors."""
    d = Path(tempfile.mkdtemp())
    try:
        shutil.copytree(ROOT / "data", d / "data")
        p = d / "data" / file
        p.write_text(edit(p.read_text(encoding="utf-8")), encoding="utf-8")
        old = build.DATA
        build.DATA = d / "data"
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                return build.load()[1]
        finally:
            build.DATA = old
    finally:
        shutil.rmtree(d)


def first_entry(text):
    """The first [[resource]] block of a data file, and where it ends."""
    i = text.index("[[resource]]")
    j = text.find("\n[[resource]]", i + 1)
    return i, (j if j > 0 else len(text))


class Validation(unittest.TestCase):
    def test_current_data_is_valid(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(build.load()[1], [])

    def test_duplicate_id(self):
        def edit(t):
            i, j = first_entry(t)
            return t + "\n" + t[i:j].replace('url = "', 'url = "https://example.org/x', 1)
        self.assertTrue(any("id" in e for e in load_with("places.toml", edit)))

    def test_regime(self):
        """A place is open or closed: its posts do not make it slow; an entry may override its group."""
        errs = load_with("places.toml", lambda t: re.sub(r'^status = "active"$', 'status = "slow"', t, count=1, flags=re.M))
        self.assertTrue(any("regime operating" in e for e in errs), errs)
        errs = load_with("places.toml", lambda t: re.sub(r'^regime = "operating"$', 'regime = "forever"', t, count=1, flags=re.M))
        self.assertTrue(any("regime must be one of" in e for e in errs), errs)
        cat = {"groups": [{"id": "g", "regime": "work"}]}
        self.assertEqual(build.regime({"group": "g"}, cat), "work")
        self.assertEqual(build.regime({"group": "g", "regime": "activity"}, cat), "activity")
        self.assertEqual(build.regime({"group": "h"}, cat), "activity")
        old = {"id": "x", "status": "active", "last_activity": "2016-10-21"}
        self.assertEqual(build.effective(dict(old, _regime="work"), {})[0], "active")
        self.assertEqual(build.effective(dict(old, _regime="activity"), {})[0], "inactive")

    def test_malformed_url(self):
        errs = load_with("places.toml", lambda t: re.sub(r'^url = "https?://', 'url = "javascript:', t, count=1, flags=re.M))
        self.assertTrue(any("url" in e for e in errs), errs)

    def test_contact_rules(self):
        def edit(t):
            i, j = first_entry(t)
            block = re.sub(r"\n\[resource\.contact\][^\[]*", "\n", t[i:j])
            return t[:i] + block.rstrip("\n") + '\n\n[resource.contact]\nphone = "04 90 00 00 00"\nemail = "a@b.com?subject=x"\nurl = "https://example.org"\ndate = "2026-11-24"\n' + t[j:]
        errs = load_with("places.toml", edit)
        self.assertTrue(any("phone" in e for e in errs), errs)
        self.assertTrue(any("email" in e for e in errs), errs)

    def test_contact_outside_places_events_clubs(self):
        def edit(t):
            i, j = first_entry(t)
            return t[:i] + t[i:j].rstrip("\n") + '\n\n[resource.contact]\nemail = "info@example.org"\nurl = "https://example.org"\ndate = "2026-11-24"\n' + t[j:]
        self.assertTrue(any("contact" in e for e in load_with("shops.toml", edit)))

    def test_funding_words(self):
        def edit(t):
            return re.sub(r'^funding = \[[^\]]*\]', 'funding = ["affiliation", "none"]', t, count=1, flags=re.M)
        self.assertTrue(any("funding" in e for e in load_with("comparators.toml", edit)))

    def test_four_sources_refused(self):
        def edit(t):
            i, j = first_entry(t)
            src = '\n[[resource.sources]]\nurl = "https://example.org/{n}"\ndate = "2026-11-24"\nkind = "read"\n'
            return t[:i] + t[i:j].rstrip("\n") + "\n" + "".join(src.format(n=n) for n in range(4)) + t[j:]
        self.assertTrue(any("source" in e for e in load_with("places.toml", edit)))


class Pages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with contextlib.redirect_stdout(io.StringIO()):
            cats, _ = build.load()
            data = build.site_data(cats, build.metrics())
        data["version"] = (ROOT / "VERSION").read_text().strip()
        cls.pages = {lang: build.page(lang, data) for lang in ("en", "fr")}

    def test_no_placeholder_left(self):
        for lang, doc in self.pages.items():
            self.assertNotRegex(doc, r"\{\{[A-Z]+\}\}", lang)

    def test_every_inline_script_is_allowed(self):
        self.assertGreaterEqual(min(len(build.inline_scripts(d)) for d in self.pages.values()), 3)
        for lang, doc in self.pages.items():
            policy = re.search(r'http-equiv="Content-Security-Policy" content="([^"]*)"', doc).group(1)
            for body in build.inline_scripts(doc):
                h = "'sha256-" + base64.b64encode(hashlib.sha256(body.encode()).digest()).decode() + "'"
                self.assertIn(h, policy, lang)

    def test_static_texts_at_first_paint(self):
        self.assertIn('data-t="nav_obs">Observatoire</a>', self.pages["fr"])
        self.assertIn('data-t="nav_obs">Observatory</a>', self.pages["en"])
        for lang, doc in self.pages.items():
            self.assertNotRegex(doc, r'data-t="\w+"[^>]*></(a|h1|h2|h3|span|button|p)>', lang)

    def test_address_of_the_website(self):
        here = {"en": build.PAGES, "fr": build.PAGES + "fr/"}
        for lang, doc in self.pages.items():
            self.assertIn(f'<link rel="canonical" href="{here[lang]}">', doc)
            self.assertNotIn("github.io", doc.split("</head>")[0], lang)
        # the job "link" of .github/workflows/preview.yml reads PAGES with this pattern, without running Python
        found = re.findall(r'^PAGES = "([^"]*)"', (ROOT / "scripts" / "build.py").read_text(encoding="utf-8"), re.M)
        self.assertEqual(found, [build.PAGES])

    def test_feed_identifiers_stay(self):  # RFC 4287, 4.2.6: an identifier does not change when the website moves
        with contextlib.redirect_stdout(io.StringIO()):
            cats, _ = build.load()
        for lang in ("en", "fr"):
            feed = build.content_feed(cats, lang)
            ids = re.findall(r"<id>([^<]*)</id>", feed)
            self.assertTrue(ids, lang)
            self.assertTrue(all(i.startswith(build.FEED_ID) for i in ids), lang)
            self.assertIn(f'rel="self" href="{build.PAGES}', feed)

    def test_data_block_cannot_close_the_script(self):
        for doc in self.pages.values():
            i = doc.index('<script id="data" type="application/json">')  # the data block ends at the first "</": it must hold no "<"
            j = doc.index("</", i + 1)
            self.assertEqual(doc[j:j + 9], "</script>")


class MachineFiles(unittest.TestCase):
    """The files for robots, language models and agents (dev/lots/acces-machines.md), from the same data as the pages."""
    @classmethod
    def setUpClass(cls):
        with contextlib.redirect_stdout(io.StringIO()):
            cls.cats, _ = build.load()
            cls.data = build.site_data(cls.cats, build.metrics())
        cls.data["version"] = (ROOT / "VERSION").read_text().strip()
        cls.md = {lang: build.readme(cls.cats, lang, "full", web=cls.data) for lang in build.LANGS}

    def test_lists_are_plain_markdown_with_absolute_links(self):
        for lang, md in self.md.items():
            self.assertNotRegex(md, r"<(img|br|p|a|picture)\b", lang)
            self.assertNotRegex(md, r"\]\((?!https?://|#)", lang)  # no link relative to the repository: the list is read on the website
            entries = md.split(f"\n## {build.T['contents'][lang]}\n")[1].split("\n## ", 1)[1]  # after the table of contents
            self.assertEqual(entries.count("\n- ["), sum(len(c["resources"]) for c in self.cats), lang)

    def test_french_list_speaks_french(self):
        self.assertIn("Couvre les sets de marque LEGO.", self.md["fr"])
        self.assertNotIn("Covers ", self.md["fr"])
        self.assertNotIn("Couvre LEGO officiel", self.md["fr"])  # in a French sentence, "de marque LEGO"

    def test_repository_lists_unchanged_by_the_web_mode(self):
        for (kind, lang), f in build.FILES.items():
            self.assertEqual(build.readme(self.cats, lang, kind), (ROOT / f).read_text(encoding="utf-8"), f)

    def test_llms_txt_follows_the_convention(self):  # llmstxt.org: H1, summary in a quotation, H2 lists of "[name](url): notes", Optional last
        lines = build.llms_txt(self.data).splitlines()
        self.assertEqual(lines[0], "# Awesome LEGO")
        self.assertTrue(lines[2].startswith("> "))
        h2 = [x for x in lines if x.startswith("## ")]
        self.assertEqual(h2[-1], "## Optional")
        items = [x for x in lines if x.startswith("- ")]
        self.assertTrue(items)
        for x in items:
            self.assertRegex(x, r"^- \[[^\]]+\]\(https://[^)\s]+\): \S", x)
        self.assertNotRegex("\n".join(lines), r"\n- (?!\[)")

    def test_sitemap_is_well_formed(self):
        import xml.etree.ElementTree as ET
        root = ET.fromstring(build.sitemap(self.data))
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9", "x": "http://www.w3.org/1999/xhtml"}
        locs = [u.find("s:loc", ns).text for u in root.findall("s:url", ns)]
        self.assertEqual(locs, [build.PAGES + p for p in ("", "fr/", build.ABOUT_PATH["en"], build.ABOUT_PATH["fr"])])
        for u in root.findall("s:url", ns):
            self.assertEqual(sorted(a.get("hreflang") for a in u.findall("x:link", ns)), ["en", "fr", "x-default"])

    def test_footer_and_about_pages_point_machines_too(self):
        for lang in build.LANGS:
            home = build.page(lang, self.data)
            self.assertIn('<a href="index.md" type="text/markdown" data-t="as_text">', home.split("<footer")[1])
            self.assertIn('type="application/json" data-t="as_json">', home.split("<footer")[1])
            about = build.about(lang, self.data)
            self.assertIn(f'rel="describedby" type="text/plain" href="{build.PAGES}llms.txt"', about.split("</head>")[0])
            self.assertIn('<a href="../index.md" type="text/markdown" data-t="as_text">', about.split("<footer")[1])

    def test_robots_allow_everything_and_give_the_sitemap(self):
        robots = build.robots_txt()
        self.assertNotRegex(robots, r"(?im)^\s*Disallow\s*:\s*\S")
        self.assertIn(f"Sitemap: {build.PAGES}sitemap.xml", robots)

    def test_home_pages_point_machines_to_the_lists(self):
        for lang in build.LANGS:
            doc = build.page(lang, self.data)
            head = doc.split("</head>")[0]
            here = build.PAGES + ("fr/" if lang == "fr" else "")
            self.assertIn(f'type="text/markdown" title="{build.MD_T["web_title"][lang]}" href="{here}index.md"', head)
            self.assertIn(f'rel="describedby" type="text/plain" href="{build.PAGES}llms.txt"', head)
            ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', head).group(1))
            dataset = next(x for x in ld["@graph"] if x["@type"] == "Dataset")
            self.assertEqual(dataset["license"], build.LICENSE_URL)
            self.assertGreaterEqual(len(dataset["description"]), 50)  # the minimum of Google's dataset search
            self.assertEqual(dataset["@id"], here + "#dataset")  # one node per page: the two descriptions are in two languages

    def test_unknown_status_or_public_falls_back_to_its_word(self):  # a value added to data/SCHEMA.md before its text: no failed build
        r = next(r for c in self.cats for r in c["resources"] if r["status"] == "active")
        cat = next(c for c in self.cats if r in c["resources"])
        one = [dict(cat, resources=[dict(r, status="paused", audience=["children", "teens"])])]
        with mock.patch.object(build, "AUDIENCES", ("children", "teens")):
            md = build.readme(one, "fr", "full", web=self.data)
        self.assertIn("Statut : paused.", md)
        self.assertIn("Pour les enfants et teens.", md)



class About(unittest.TestCase):
    """site/about/ and site/fr/about/: plain text pages, figures from the data, the header of the home pages."""
    @classmethod
    def setUpClass(cls):
        with contextlib.redirect_stdout(io.StringIO()):
            cats, _ = build.load()
            cls.data = build.site_data(cats, build.metrics())
        cls.data["version"] = (ROOT / "VERSION").read_text().strip()
        cls.pages = {lang: build.about(lang, cls.data) for lang in ("en", "fr")}

    def test_no_placeholder_left(self):
        for lang, doc in self.pages.items():
            self.assertNotRegex(doc, r"\{\{|\{(REPO|HOME|groups|date|active)\}", lang)

    def test_every_inline_script_is_allowed(self):
        for lang, doc in self.pages.items():
            policy = re.search(r'http-equiv="Content-Security-Policy" content="([^"]*)"', doc).group(1)
            for body in build.inline_scripts(doc):
                h = "'sha256-" + base64.b64encode(hashlib.sha256(body.encode()).digest()).decode() + "'"
                self.assertIn(h, policy, lang)

    def test_found_by_search_engines(self):
        for lang, doc in self.pages.items():
            self.assertIn(f'<link rel="canonical" href="{build.PAGES}{build.ABOUT_PATH[lang]}">', doc)
            self.assertIn(f'hreflang="en" href="{build.PAGES}about/"', doc)
            self.assertIn(f'hreflang="fr" href="{build.PAGES}fr/about/"', doc)
            ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', doc).group(1))
            self.assertEqual(ld["@type"], "AboutPage")

    def test_figures_follow_the_data(self):
        R = self.data["resources"]
        for doc in self.pages.values():
            self.assertIn(f"<b>{len(R)}</b>", doc)
            self.assertIn(f"<b>{sum(1 for r in R if r['featured'])}</b>", doc)
            self.assertIn(f"<b>{sum(len(r['sources']) for r in R)}</b>", doc)

    def test_no_line_length_cap(self):
        """Text fills its block: no max-width in ch or em on the website (rule of the maintainer, 05/11/2026)."""
        for f in sorted((ROOT / "site-src").glob("*.css")) + sorted((ROOT / "site-src").glob("*.html")):
            self.assertNotRegex(f.read_text(encoding="utf-8"), r"max-(width|inline-size):\s*[0-9.]+(ch|em)\b", f.name)

    def test_same_header_and_footer_as_the_home_pages(self):
        home = {lang: build.page(lang, self.data) for lang in ("en", "fr")}
        for lang, doc in self.pages.items():
            for part in ("<footer>", "data-t=\"about\"", "id=\"setmenu\"", "vault/#open"):
                self.assertIn(part, doc, lang)
                self.assertIn(part, home[lang], lang)
            self.assertIn('class="dsk" href="./" data-t="about" aria-current="page"', doc)

    def test_plate_draws_one_stud_per_resource(self):
        """The plate of the selection: as many studs of each kind as resources of that kind, at most three
        rectangles per kind, whatever the counts (none of a kind, whole rows, a single stud); the row of phones in proportion."""
        cols = build.PLATE_COLS
        for counts in ((54, 497, 198), (0, 0, 1), (0, 50, 0), (25, 25, 30), (1, 0, 0), (49, 2, 99)):
            doc = build.plate(counts, "label")
            studs = {k: 0 for k in ("sel", "rank", "list")}
            for kind, w, h in re.findall(r'fill="url\(#stud-(\w+)\)" x="\d+" y="\d+" width="(\d+)" height="(\d+)"', doc):
                studs[kind] += int(w) // 10 * int(h) // 10
                self.assertLessEqual(int(w), cols * 10, counts)
            self.assertEqual(tuple(studs.values()), counts)
            for kind in studs:
                self.assertLessEqual(doc.count(f"url(#stud-{kind})"), 3, (counts, kind))
            band = dict(re.findall(r'<span class="k-(\w+)" style="flex:(\d+)">', doc))
            self.assertEqual({k: int(v) for k, v in band.items()}, {k: v for k, v in zip(studs, counts) if v})

    def test_way_draws_each_step_at_one_scale(self):
        """The way of an entry: one drawing per step, on boxes of one size (the same scale), each brick or plate with
        its studs (one per square of its top, unless another piece sits on it), the entry in each, the texts in order."""
        doc = build.way([(f"n{i}", f"t{i}") for i in range(len(build.WAY))])
        boxes = re.findall(r'<svg class="iso" viewBox="\S+ \S+ (\S+) (\S+)"', doc)
        self.assertEqual(len(boxes), len(build.WAY))
        self.assertEqual(len(set(boxes)), 1)
        parts = doc.split("<li>")[1:]
        for step, part in zip(build.WAY, parts):
            hidden = build.covered(step)
            studs = sum(1 for a, b, z, w, d, h, _, kind in step if kind == "brick" for i in range(w) for j in range(d)
                        if (a + i + .5, b + j + .5, z + h) not in hidden)
            self.assertEqual(part.count('href="#way-stud"'), studs)
            self.assertEqual(sum(1 for *_, colour, _ in step if colour == "y"), 1)
        self.assertEqual(re.findall(r"<b>(n\d)</b><p>(t\d)</p>", doc), [(f"n{i}", f"t{i}") for i in range(len(build.WAY))])

    def test_icon_buttons_named_without_the_page_script(self):
        self.assertIn('id="settings" type="button" aria-expanded="false" aria-controls="setmenu" data-t-label="settings" aria-label="Réglages"', self.pages["fr"])
        self.assertIn('data-t="nav_dir">Directory</a>', self.pages["en"])


def entry_of(text, rid):
    """Span of the [[resource]] block with id `rid`."""
    i = text.index(f'id = "{rid}"')
    i = text.rindex("[[resource]]", 0, i)
    j = text.find("\n[[resource]]", i + 1)
    return i, (j if j > 0 else len(text))


def set_field(rid, key, value):
    """An edit that sets `key = value` (TOML) in the entry `rid`, replacing its current line or adding one after its id."""
    def edit(t):
        m = re.search(rf'(?ms)^id = "{re.escape(rid)}"\n.*?(?=^\[\[resource\]\]|\Z)', t)
        block = m.group(0)
        line = f"{key} = {value}\n"
        new = re.sub(rf"(?m)^{re.escape(key)} = .*\n", lambda _: line, block, count=1) if re.search(rf"(?m)^{re.escape(key)} = ", block) else block.replace(f'id = "{rid}"\n', f'id = "{rid}"\n{line}', 1)
        return t[:m.start()] + new + t[m.end():]
    return edit


def notes_with(file, edit):
    """Warnings of the rules of lot 3 (load, ranks, texts) on a copy of data/ changed by `edit`."""
    d = Path(tempfile.mkdtemp())
    try:
        shutil.copytree(ROOT / "data", d / "data")
        p = d / "data" / file
        p.write_text(edit(p.read_text(encoding="utf-8")), encoding="utf-8")
        old = build.DATA
        build.DATA = d / "data"
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                cats, _ = build.load()
            build.rank_check(cats)
            build.text_notes(cats)
            return list(build.notes)
        finally:
            build.DATA = old
    finally:
        shutil.rmtree(d)


class Lot3Model(unittest.TestCase):
    """Fields of v3.0 (data/SCHEMA.md): their form fails the build, their content rules warn until lot 3b."""
    def test_current_data_has_no_form_error(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(build.load()[1], [])

    def test_rank_form(self):
        for bad in ('rank = {intl = 6}', 'rank = {fr = 1}', 'rank = {intl = true}', 'rank = 1'):
            k, v = bad.split(" = ", 1)
            errs = load_with("comparators.toml", set_field("brick-broker", k, v))  # price comparators: ranked per country
            self.assertTrue(any("rank is a table" in e for e in errs), (bad, errs))
        self.assertEqual(load_with("comparators.toml", set_field("brick-broker", "rank", "{intl = 2, FR = 1}")), [])

    def test_one_entry_per_rank(self):
        two = lambda t: set_field("brickmitri", "rank", "{FR = 1}")(set_field("brick-broker", "rank", "{FR = 1}")(t))
        load_with("comparators.toml", two)
        cats, _ = load_quiet(two)
        build.rank_check(cats)
        self.assertTrue(any("rank 1 given to" in n for n in build.notes), build.notes)

    def test_group_rank_scope(self):
        errs = load_with("places.toml", lambda t: t.replace('rank_scope = "country"\n', "", 1))
        self.assertTrue(any("rank_scope" in e for e in errs), errs)

    def test_city_names(self):
        self.assertTrue(any("city_fr" in e for e in load_with("places.toml", lambda t: t.replace('city_fr = "Londres"', 'city_fr = "London"', 1))))
        self.assertTrue(any("one city" in n for n in notes_with("places.toml", lambda t: t.replace('city = "Paderborn"', 'city = "Paderborn, Lippstadt"', 1))))

    def test_access_by_category(self):
        ns = notes_with("places.toml", lambda t: t.replace('access = "paid"', 'access = "freemium"', 1))
        self.assertTrue(any("access 'freemium' says nothing for entry" in n for n in ns), ns)

    def test_size_form(self):
        errs = load_with("places.toml", set_field("lego-house", "size", '[{n = 12000, unit = "acres"}]'))
        self.assertTrue(any("size is a list" in e for e in errs), errs)
        self.assertEqual(load_with("places.toml", set_field("lego-house", "size", '[{n = 12000, unit = "square-metres"}, {n = 25000000, unit = "bricks", approx = "about"}]')), [])

    def test_operator(self):
        self.assertTrue(any("operator" in e for e in load_with("places.toml", lambda t: t.replace('operator = "lego-group"', 'operator = "merlin"', 1))))

    def test_audience(self):
        for bad in ('"children"', '[]', '["kids"]', '["adults", "adults"]'):
            errs = load_with("places.toml", set_field("lego-house", "audience", bad))
            self.assertTrue(any("audience is a list" in e for e in errs), (bad, errs))
        self.assertEqual(load_with("places.toml", set_field("lego-house", "audience", '["children", "adults"]')), [])

    def test_no_rank_on_a_dead_entry(self):
        def edit(t):
            t = set_field("lego-house", "status", '"dead"')(t)
            return set_field("lego-house", "rank", "{intl = 1}")(t)
        self.assertTrue(any("rank on an entry whose status is dead" in n for n in notes_with("places.toml", edit)))


class Lot3Texts(unittest.TestCase):
    def test_brand_in_french_sentences(self):
        ns = notes_with("places.toml", set_field("lego-house", "summary_fr", '"Des sets LEGO officiels."'))
        self.assertTrue(any("lego-house: summary_fr" in n and "LEGO officiels" in n for n in ns), [n for n in ns if "lego-house" in n])

    def test_numeric_dates(self):
        ns = notes_with("places.toml", set_field("lego-house", "summary_en", '"Opened 2026-07-01."'))
        self.assertTrue(any("lego-house" in n and "2026-07-01" in n for n in ns), [n for n in ns if "lego-house" in n])

    def test_site_phrases_follow_the_brand_rule(self):
        build.notes.clear()
        build.site_notes()
        self.assertEqual(build.notes, [])

    def test_labels_exist(self):
        self.assertEqual(build.check_docs(), [])


class Needs(unittest.TestCase):
    def test_unknown_group_fails(self):
        cats, _ = load_quiet(lambda t: t)
        ids = {r["id"] for c in cats for r in c["resources"]}
        good = build.needs(cats, ids)
        self.assertGreaterEqual(len(good), 10)
        old = build.DATA
        d = Path(tempfile.mkdtemp())
        try:
            shutil.copytree(ROOT / "data", d / "data")
            p = d / "data" / "journeys.toml"
            p.write_text(p.read_text(encoding="utf-8").replace('"shops/official-lego"', '"shops/nothing"', 1), encoding="utf-8")
            build.DATA = d / "data"
            with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
                build.needs(cats, ids)
        finally:
            build.DATA = old
            shutil.rmtree(d)

    def test_need_audience(self):
        cats, _ = load_quiet(lambda t: t)
        ids = {r["id"] for c in cats for r in c["resources"]}
        old = build.DATA
        d = Path(tempfile.mkdtemp())
        try:
            shutil.copytree(ROOT / "data", d / "data")
            p = d / "data" / "journeys.toml"
            p.write_text(p.read_text(encoding="utf-8").replace('audience = "children"', 'audience = "kids"', 1), encoding="utf-8")
            build.DATA = d / "data"
            with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
                build.needs(cats, ids)
        finally:
            build.DATA = old
            shutil.rmtree(d)

    def test_same_site_leaves_out_platforms(self):
        with contextlib.redirect_stdout(io.StringIO()):
            cats, _ = build.load()
            rows = {r["id"]: r for r in build.site_data(cats, {})["resources"]}
        self.assertEqual(rows["jangbricks"]["same"], [])  # youtube.com
        self.assertIn("brickset-api-v3", rows["brickset"]["same"])


def load_quiet(edit):
    d = Path(tempfile.mkdtemp())
    try:
        shutil.copytree(ROOT / "data", d / "data")
        p = d / "data" / "comparators.toml"
        p.write_text(edit(p.read_text(encoding="utf-8")), encoding="utf-8")
        old = build.DATA
        build.DATA = d / "data"
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                return build.load()
        finally:
            build.DATA = old
    finally:
        shutil.rmtree(d)


class Details(unittest.TestCase):
    def test_strengths_leave_the_page_for_details_json(self):
        with contextlib.redirect_stdout(io.StringIO()):
            cats, _ = build.load()
            data = build.site_data(cats, {})
        data["version"] = "0"
        for lang in ("en", "fr"):
            doc = build.page(lang, data)
            blob = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>', doc, re.S).group(1).replace("\\u003c", "<"))
            self.assertFalse(any("strengths" in r[lang] for r in blob["resources"]))
            det = json.loads(build.details(lang, data))
            n = sum(1 for r in data["resources"] if r[lang]["strengths"] or r[lang]["weaknesses"])
            self.assertEqual(len(det), n)
            self.assertEqual(sum(1 for r in blob["resources"] if r[lang]["d"]), n)
            app = (ROOT / "site-src" / "app.js").read_text(encoding="utf-8") + (ROOT / "site-src" / "header.js").read_text(encoding="utf-8")
            for k in build.PAGE_UNREAD:  # left out of the page because the page never reads them
                self.assertFalse(any(k in r for r in blob["resources"]), k)
                self.assertNotRegex(app, rf"\.{k}\b", k)
            self.assertFalse(any(v is None or v == [] or v == {} or v is False for r in blob["resources"] for v in r.values()))  # empty values read as absent

    def test_metrics_file_holds_the_measurements_alone(self):
        """site/metrics.json: what refresh.py --from-site reads back, the measured entries and nothing else."""
        data = {"resources": [{"id": "a", "metrics": {"stars": 2}, "name": "A"}, {"id": "b", "metrics": {}, "name": "B"}]}
        self.assertEqual(json.loads(build.site_metrics(data)), {"a": {"stars": 2}})

    def test_recurrence_reaches_the_card(self):
        """AL-57: the recurrence of an entry (recurrence_en, recurrence_fr) is carried by the page and drawn on its card."""
        with contextlib.redirect_stdout(io.StringIO()):
            cats, _ = build.load()
            data = build.site_data(cats, {})
        data["version"] = "0"
        want = {r["id"]: r for c in cats for r in c["resources"] if r.get("recurrence_en")}
        self.assertGreater(len(want), 50)
        for lang in ("en", "fr"):
            blob = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>', build.page(lang, data), re.S).group(1).replace("\\u003c", "<"))
            got = {r["id"]: r[lang].get("rec") for r in blob["resources"]}
            for i, r in want.items():
                self.assertEqual(got[i], build.text(r, "recurrence", lang), f"{lang} {i}")
            self.assertFalse(any(v for i, v in got.items() if i not in want))
        self.assertRegex((ROOT / "site-src" / "app.js").read_text(encoding="utf-8"), r"x\.rec\?")  # the card's legend reads it


class Changelog(unittest.TestCase):
    def test_a_long_entry_is_refused(self):
        self.assertEqual(build.changelog_long("## v9.1 — 2026-01-01\nShort.\n\n## v9.0 — 2026-01-01\n" + "x" * 551 + "\n"), ["v9.0: 551 characters"])
        self.assertEqual(build.changelog_long((ROOT / "CHANGELOG.md").read_text(encoding="utf-8")), [])


class Dates(unittest.TestCase):
    def test_in_letters(self):
        self.assertEqual(build.in_letters("2027-07-03", "en"), "3 Jul 2027")
        self.assertEqual(build.in_letters("2027-04-01", "fr"), "1er avr. 2027")
        self.assertEqual(build.in_letters("2027-04-01", "en"), "1 Apr 2027")
        self.assertEqual(build.in_letters("2027-09-30", "en"), "30 Sep 2027")

    def test_feed_has_no_numeric_date_in_titles(self):
        with contextlib.redirect_stdout(io.StringIO()):
            cats, _ = build.load()
        for lang in ("en", "fr"):
            titles = re.findall(r"<title>(.*?)</title>", build.content_feed(cats, lang))
            self.assertFalse([x for x in titles if build.NUMERIC_DATE.search(x)])

    def test_feed_is_named_after_the_site_and_has_no_event_date(self):
        with contextlib.redirect_stdout(io.StringIO()):
            cats, _ = build.load()
        for lang in ("en", "fr"):
            feed = build.content_feed(cats, lang)
            self.assertEqual(re.search(r"<title>(.*?)</title>", feed).group(1), "Awesome LEGO")
            self.assertNotIn("#next-", feed)

    def test_feed_batches_a_day_of_many_additions(self):
        """More than FEED_BATCH entries added on one day make one announcement; fewer stay one item each."""
        with contextlib.redirect_stdout(io.StringIO()):
            cats, _ = build.load()
        rs = [r for c in cats for r in c["resources"]]
        for r in rs:
            r["added"] = build.BASELINE
        for r in rs[:build.FEED_BATCH + 1]:
            r["added"] = "2030-01-02"
        for r in rs[build.FEED_BATCH + 1:build.FEED_BATCH + 3]:
            r["added"] = "2030-01-03"
        for lang, word in (("en", "resources added"), ("fr", "ressources ajoutées")):
            titles = re.findall(r"<title>(.*?)</title>", build.content_feed(cats, lang))
            self.assertEqual(sum(1 for x in titles if word in x), 1)
            self.assertIn(f"{build.FEED_BATCH + 1} {word}", " ".join(titles))
            self.assertEqual(sum(1 for x in titles if x.startswith(build.FEED_T["new"][lang] + " ·")), 2)


class Selection(unittest.TestCase):
    def test_readme_lists_the_rank_one_of_each_group(self):
        """The selection: the rank 1 worldwide of each group (lot 3b); `featured` is refused."""
        with contextlib.redirect_stdout(io.StringIO()):
            cats, _ = build.load()
        text = build.readme(cats, "en")
        ones = [r for c in cats for r in c["resources"] if (r.get("rank") or {}).get("intl") == 1]
        self.assertEqual(len([l for l in text.splitlines() if l.startswith("- [") and "](http" in l]), len({r["url"] for r in ones}))  # a brand and its shop share one line
        self.assertEqual(len(ones), sum(len(c["category"]["groups"]) for c in cats))
        self.assertTrue(any("featured is replaced by rank" in e for e in load_with("places.toml", set_field("lego-house", "featured", "true"))))


class Lot3Checks(unittest.TestCase):
    def test_operator_from_the_field(self):
        with contextlib.redirect_stdout(io.StringIO()):
            cats, _ = build.load()
            rows = {r["id"]: r for r in build.site_data(cats, {})["resources"]}
        self.assertEqual(rows["lego-house"]["operator"], "lego-group")
        self.assertEqual(rows["libraries-ni-lego-club"]["operator"], "licensee")
        self.assertIsNone(rows["jangbricks"]["operator"])

    def test_french_card_text(self):
        def planted(t):
            i, j = entry_of(t, "brickset")
            return t[:i] + re.sub(r'summary_fr = "[^"]*"', 'summary_fr = "Base de données allemande de sets et de figurines."', t[i:j], count=1) + t[j:]
        before = notes_with("comparators.toml", lambda t: t)
        self.assertFalse([n for n in before if "brickset: summary_fr starts with a country" in n])
        ns = notes_with("comparators.toml", planted)
        self.assertTrue([n for n in ns if "brickset: summary_fr starts with a country" in n], "a demonym after the noun is found")
        def lang_only(t):
            i, j = entry_of(t, "jangbricks")
            return t[:i] + re.sub(r'summary_fr = "[^"]*"', 'summary_fr = "Chaîne en allemand sur les sets de marque LEGO."', t[i:j], count=1) + t[j:]
        ns = notes_with("video.toml", lang_only)
        self.assertFalse([n for n in ns if "jangbricks: summary_fr starts with a country" in n], "a language is not a country")

class EnglishOnly(unittest.TestCase):
    """Contributions in English only (decision of 24/11/2026, 13:47): no French text is refused, shown in English."""
    @staticmethod
    def drop_french(t):
        m = re.search(r'(?ms)^id = "lego-house"\n.*?(?=^\[\[resource\]\]|\Z)', t)
        block = re.sub(r"(?m)^(summary|strengths|weaknesses|recurrence)_fr = .*\n", "", m.group(0))
        return t[:m.start()] + block + t[m.end():]

    def test_entry_without_french_builds_and_shows_english(self):
        self.assertEqual(load_with("places.toml", self.drop_french), [])
        cats, _ = load_quiet(lambda t: t)
        old = build.DATA
        d = Path(tempfile.mkdtemp())
        try:
            shutil.copytree(ROOT / "data", d / "data")
            p = d / "data" / "places.toml"
            p.write_text(self.drop_french(p.read_text(encoding="utf-8")), encoding="utf-8")
            build.DATA = d / "data"
            with contextlib.redirect_stdout(io.StringIO()):
                cats, errs = build.load()
            self.assertEqual(errs, [])
            self.assertTrue(any("lego-house" in w for w in build.untranslated))
            row = next(r for r in build.site_data(cats, {})["resources"] if r["id"] == "lego-house")
            self.assertEqual(row["fr"]["tl"], "en")
            self.assertEqual(row["fr"]["summary"], row["en"]["summary"])
            self.assertNotIn("tl", row["en"])
        finally:
            build.DATA = old
            shutil.rmtree(d)

    def test_french_texts_come_together(self):
        def partial(t):
            t = self.drop_french(t)
            return set_field("lego-house", "strengths_fr", '["Un point"]')(t)
        self.assertTrue(any("French texts come together" in e for e in load_with("places.toml", partial)))


def tiny_png(text=None):
    """A 1 x 1 PNG, with a tEXt chunk `version` when text is given (standard library only)."""
    import struct
    import zlib

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    out = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 0, 0, 0, 0))
    if text is not None:
        out += chunk(b"tEXt", b"version\0" + text.encode("latin-1"))
    return out + chunk(b"IDAT", zlib.compress(b"\0\0")) + chunk(b"IEND", b"")


class ReadmeImage(unittest.TestCase):
    def test_reads_the_version_of_a_png(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "a.png"
            f.write_bytes(tiny_png("3.5"))
            self.assertEqual(build.png_text(f, "version"), "3.5")
            f.write_bytes(tiny_png())
            self.assertIsNone(build.png_text(f, "version"))

    def test_an_image_of_another_version_is_reported(self):  # reported as a warning by build.py, never an error (decision of 25/11/2026)
        self.assertEqual(len(build.check_readme_images("0.1")), len(build.README_IMAGES))


if __name__ == "__main__":
    unittest.main()
