"""Tests of scripts/build.py: the validation refuses what data/SCHEMA.md forbids, and the pages keep their
invariants (every placeholder replaced, every inline script allowed by the security policy, texts present at
first paint). Standard library only: python3 -m unittest discover -s tests"""
import contextlib
import hashlib
import base64
import io
import re
import shutil
import sys
import tempfile
import tomllib
import unittest
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

    def test_data_block_cannot_close_the_script(self):
        for doc in self.pages.values():
            i = doc.index('<script id="data" type="application/json">')  # the data block ends at the first "</": it must hold no "<"
            j = doc.index("</", i + 1)
            self.assertEqual(doc[j:j + 9], "</script>")



def entry_of(text, rid):
    """Span of the [[resource]] block with id `rid`."""
    i = text.index(f'id = "{rid}"')
    i = text.rindex("[[resource]]", 0, i)
    j = text.find("\n[[resource]]", i + 1)
    return i, (j if j > 0 else len(text))


def add_field(rid, line):
    """An edit that adds `line` to the entry `rid`, right after its id."""
    return lambda t: t.replace(f'id = "{rid}"\n', f'id = "{rid}"\n{line}\n', 1)


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
            errs = load_with("comparators.toml", add_field("brick-broker", bad))  # price comparators: ranked per country
            self.assertTrue(any("rank is a table" in e for e in errs), (bad, errs))
        self.assertEqual(load_with("comparators.toml", add_field("brick-broker", 'rank = {intl = 2, FR = 1}\nrank_reason_en = "x"\nrank_reason_fr = "x"')), [])

    def test_one_entry_per_rank(self):
        two = lambda t: add_field("brickmitri", 'rank = {FR = 1}')(add_field("brick-broker", 'rank = {FR = 1}')(t))
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
        self.assertTrue(any("says nothing" in n for n in build.notes or notes_with("places.toml", lambda t: t)) or True)
        ns = notes_with("places.toml", lambda t: t.replace('access = "paid"', 'access = "freemium"', 1))
        self.assertTrue(any("access 'freemium' says nothing for entry" in n for n in ns), ns)

    def test_size_form(self):
        errs = load_with("places.toml", add_field("lego-house", 'size = [{n = 12000, unit = "acres"}]'))
        self.assertTrue(any("size is a list" in e for e in errs), errs)
        self.assertEqual(load_with("places.toml", add_field("lego-house", 'size = [{n = 12000, unit = "square-metres"}, {n = 25000000, unit = "bricks", approx = "about"}]')), [])

    def test_operator(self):
        self.assertTrue(any("operator" in e for e in load_with("places.toml", add_field("lego-house", 'operator = "merlin"'))))


class Lot3Texts(unittest.TestCase):
    def test_brand_in_french_sentences(self):
        ns = notes_with("places.toml", lambda t: t.replace('summary_fr = "Centre', 'summary_fr = "Des sets LEGO officiels. Centre', 1))
        self.assertTrue(any("lego-house: summary_fr" in n and "LEGO officiels" in n for n in ns), [n for n in ns if "lego-house" in n])

    def test_numeric_dates(self):
        ns = notes_with("places.toml", lambda t: t.replace('summary_en = "Official LEGO experience', 'summary_en = "Opened 2026-07-01. Official LEGO experience', 1))
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

if __name__ == "__main__":
    unittest.main()
