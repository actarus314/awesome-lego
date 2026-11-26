"""Tests of scripts/previews.py: a preview page is marked (banner, noindex) without breaking the page."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
import previews  # noqa: E402


class Mark(unittest.TestCase):
    PAGE = '<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><title>t</title></head><body class="x"><p>a</p></body></html>'

    def test_pull_request(self):
        out = previews.mark(self.PAGE, 17, "d727dac", "https://github.com/o/r/pull/17")
        self.assertIn('<head><meta name="robots" content="noindex, nofollow">', out)
        self.assertIn('<body class="x"><div role="note"', out)
        self.assertIn("demande de fusion #17 (commit d727dac)", out)
        self.assertEqual(out.count('role="note"'), 1)
        self.assertNotIn("<script", out)  # nothing the page's security policy would refuse
        self.assertIn("<title>Aperçu #17 · t</title>", out)
        self.assertIn("header.top{background:color-mix(in srgb,#c62828", out)  # the sticky header stays marked while scrolling

    def test_branch_in_english(self):
        out = previews.mark(self.PAGE.replace('lang="fr"', 'lang="en"'), "dev", "abc1234", "https://github.com/o/r/tree/dev")
        self.assertIn("Preview of the branch dev (commit abc1234)", out)
        self.assertIn("Open the branch", out)

    def test_escaped(self):
        out = previews.mark(self.PAGE, 3, "<b>", 'https://x/"y')
        self.assertIn("&lt;b&gt;", out)
        self.assertIn("&quot;y", out)

    def test_index(self):
        out = previews.index([{"n": 5, "title": "A <b>", "sha": "1", "url": "u", "failed": False},
                              {"n": "dev", "title": "branch dev", "sha": "2", "url": "v", "failed": True},
                              {"n": 9, "title": "B", "sha": "3", "url": "w", "failed": False}])
        self.assertLess(out.index('href="dev/"'), out.index('href="9/"'))
        self.assertLess(out.index('href="9/"'), out.index('href="5/"'))
        self.assertIn("A &lt;b&gt;", out)
        self.assertIn("build failed", out)
        self.assertIn("noindex", out)


if __name__ == "__main__":
    unittest.main()
