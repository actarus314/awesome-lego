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
        self.assertIn("demande de fusion #17 (commit d727dac, fusionné avec main)", out)
        self.assertEqual(out.count('role="note"'), 1)
        self.assertNotIn("<script", out)  # nothing the page's security policy would refuse
        self.assertIn("<title>Aperçu #17 · t</title>", out)
        self.assertIn("header.top,#vault header{background:color-mix(in srgb,#c62828", out)  # the sticky header stays marked while scrolling

    def test_in_english(self):
        out = previews.mark(self.PAGE.replace('lang="fr"', 'lang="en"'), 4, "abc1234", "https://github.com/o/r/pull/4")
        self.assertIn("Preview of pull request #4 (commit abc1234, merged with main)", out)
        self.assertIn("(commit abc1234, alone: it conflicts with main)", previews.mark(self.PAGE.replace('lang="fr"', 'lang="en"'), 4, "abc1234", "u", merged=False))
        self.assertIn("Open the pull request", out)
        self.assertIn("<title>Preview #4 · t</title>", out)

    def test_the_number_its_merge_gives(self):
        en = self.PAGE.replace('lang="fr"', 'lang="en"')
        self.assertIn("(commit abc1234, merged with main), its merge gives v4.10: not the published website.", previews.mark(en, 4, "abc1234", "u", True, "4.10"))
        self.assertIn("(commit abc1234, merged with main), its merge gives no new number: not", previews.mark(en, 4, "abc1234", "u", True, ""))
        self.assertIn("(commit abc1234, merged with main): not", previews.mark(en, 4, "abc1234", "u"))   # unknown: a failed build
        self.assertIn("sa fusion donne la v4.9.1 : ce n&#x27;est pas le site publié.", previews.mark(self.PAGE, 4, "abc1234", "u", True, "4.9.1"))

    def test_escaped(self):
        out = previews.mark(self.PAGE, 3, "<b>", 'https://x/"y')
        self.assertIn("&lt;b&gt;", out)
        self.assertIn("&quot;y", out)

    def test_index(self):
        out = previews.index([{"n": 5, "title": "A <b>", "sha": "1", "url": "u", "failed": False},
                              {"n": 7, "title": "C", "sha": "2", "url": "v", "failed": True},
                              {"n": 9, "title": "B", "sha": "3", "url": "w", "failed": False}])
        self.assertLess(out.index('href="9/"'), out.index('href="7/"'))
        self.assertLess(out.index('href="7/"'), out.index('href="5/"'))
        self.assertIn("A &lt;b&gt;", out)
        self.assertIn("build failed", out)
        self.assertIn("noindex", out)


class MergeWithMain(unittest.TestCase):
    """The preview is the pull request merged with main; the branch alone when they conflict."""
    def repo(self):
        import subprocess
        import tempfile
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        d = pathlib.Path(tmp.name)
        git = lambda *a: subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=d, check=True, capture_output=True, text=True).stdout.strip()
        git("init", "-q", "-b", "main")
        (d / "a.txt").write_text("one\n")
        (d / "b.txt").write_text("one\n")
        git("add", "-A"); git("commit", "-qm", "base")
        return d, git

    def test_merged_when_the_changes_meet_no_conflict(self):
        d, git = self.repo()
        git("checkout", "-qb", "pr"); (d / "a.txt").write_text("branch\n"); git("commit", "-qam", "pr")
        pr = git("rev-parse", "HEAD")
        git("checkout", "-q", "main"); (d / "b.txt").write_text("main moved\n"); git("commit", "-qam", "main")
        self.assertTrue(previews.merge_with_main(d, pr))
        self.assertEqual(((d / "a.txt").read_text(), (d / "b.txt").read_text()), ("branch\n", "main moved\n"))

    def test_the_branch_alone_when_it_conflicts(self):
        d, git = self.repo()
        git("checkout", "-qb", "pr"); (d / "a.txt").write_text("branch\n"); git("commit", "-qam", "pr")
        pr = git("rev-parse", "HEAD")
        git("checkout", "-q", "main"); (d / "a.txt").write_text("main\n"); git("commit", "-qam", "main")
        self.assertFalse(previews.merge_with_main(d, pr))
        self.assertEqual((git("rev-parse", "HEAD"), (d / "a.txt").read_text()), (pr, "branch\n"))


if __name__ == "__main__":
    unittest.main()
