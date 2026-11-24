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
        self.assertIn('data-t="nav_out">Sortir</a>', self.pages["fr"])
        self.assertIn('data-t="nav_out">Out and about</a>', self.pages["en"])
        for lang, doc in self.pages.items():
            self.assertNotRegex(doc, r'data-t="\w+"[^>]*></(a|h1|h2|h3|span|button|p)>', lang)

    def test_data_block_cannot_close_the_script(self):
        for doc in self.pages.values():
            i = doc.index('<script id="data" type="application/json">')  # the data block ends at the first "</": it must hold no "<"
            j = doc.index("</", i + 1)
            self.assertEqual(doc[j:j + 9], "</script>")


class Calendar(unittest.TestCase):
    def test_lines_folded_and_closed(self):
        with contextlib.redirect_stdout(io.StringIO()):
            cats, _ = build.load()
        for lang in ("en", "fr"):
            ics = build.calendar(cats, lang)
            self.assertTrue(ics.startswith("BEGIN:VCALENDAR") and ics.rstrip().endswith("END:VCALENDAR"))
            self.assertEqual(ics.count("BEGIN:VEVENT"), ics.count("END:VEVENT"))
            for line in ics.split("\r\n"):
                self.assertLessEqual(len(line.encode()), 75, line)


if __name__ == "__main__":
    unittest.main()
