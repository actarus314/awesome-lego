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

    def test_link_to_the_commits(self):
        out = previews.mark(self.PAGE, 61, "abc1234", "u", commits="https://x/preview/61/c/")
        self.assertIn('Tous les commits de la demande', out)
        self.assertIn('href="https://x/preview/61/c/"', out)
        self.assertIn('href="https://x/preview/61/compare/" style="color:#fff">Côte à côte</a>', out)
        self.assertNotIn("Tous les commits", previews.mark(self.PAGE, 61, "abc1234", "u"))

    def test_commit_list(self):
        rows = [{"sha": "a" * 40, "href": "aaaaaaa/", "head": False, "date": "2026-11-28", "subject": "first <b>", "note": ""},
                {"sha": "c" * 40, "href": "ccccccc/", "head": False, "date": "2026-11-28", "subject": "variant A", "note": "the brick <i>"},
                {"sha": "b" * 40, "href": "../", "head": True, "date": "2026-11-28", "subject": "second", "note": ""}]
        out = previews.commit_list(61, "u", rows)
        self.assertLess(out.index('href="aaaaaaa/"'), out.index('href="../"'))  # oldest first, newest last
        self.assertIn("Oldest first, newest last", out)
        self.assertIn("1 of 3 (oldest)", out)
        self.assertIn("3 of 3 (newest)", out)
        self.assertIn("<li><b>2 of 3 · <a", out)  # the version to compare, in bold, with its note
        self.assertIn("To compare: the brick &lt;i&gt;", out)
        self.assertIn("first &lt;b&gt;", out)
        self.assertIn(f'href="{previews.PAGES}"', out)  # the published website, as the reference
        self.assertIn('href="../compare/"', out)
        self.assertIn("noindex", out)
        same = previews.commit_list(61, "u", [{**rows[2], "made": "d" * 40}])
        self.assertIn('>ddddddd</a>', same)  # the commit that made the website, not the head that only touched notes
        self.assertIn("(head bbbbbbb: same website)", same)

    def test_compare_page(self):
        rows = [{"sha": "a" * 40, "head": False, "subject": "A </script><b>", "note": "the brick"},
                {"sha": "b" * 40, "head": True, "subject": "B", "note": ""}]
        out = previews.compare_page(61, rows)
        self.assertIn("Pull request #61 side by side", out)
        self.assertNotIn("{{", out)
        self.assertNotIn("</script><b>", out)  # data never closes the script
        self.assertIn('"root": "../c/aaaaaaa/"', out)
        self.assertIn('"root": "../"', out)
        self.assertIn('"root": "../../../"', out)  # the published website, from preview/<n>/compare/
        self.assertIn('"note": "the brick"', out)

    def test_no_line_length_cap(self):
        """The pages written by this script, like the website's, let text fill its block (rule of the maintainer)."""
        import re
        for f in ("previews.py", "compare.html"):
            src = (pathlib.Path(previews.__file__).resolve().parent / f).read_text()
            self.assertIsNone(re.search(r"(?<!\()max-(width|inline-size)\s*:", src), f)  # a media query is no cap

    def test_unchanged_in_the_index(self):
        out = previews.index([{"n": 63, "title": "t", "sha": "1", "url": "u", "failed": False, "unchanged": True}])
        self.assertIn("changes nothing on the published website: no preview", out)
        self.assertNotIn('href="63/"', out)

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


class History(unittest.TestCase):
    """The earlier commits kept for a preview: those that change the website, the head always, MAX_COMMITS at most."""
    def test_commits_that_change_the_website(self):
        import subprocess
        import tempfile
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        d = pathlib.Path(tmp.name)
        git = lambda *a: subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=d, check=True, capture_output=True, text=True).stdout.strip()
        git("init", "-q", "-b", "main")
        (d / "site-src").mkdir(); (d / "dev").mkdir()
        (d / "site-src" / "a.css").write_text("0\n"); git("add", "-A"); git("commit", "-qm", "base")
        git("checkout", "-qb", "pr")
        made = []
        for i, path in enumerate(["site-src/a.css", "dev/notes.md", "site-src/a.css", "dev/notes.md"]):
            (d / path).write_text(f"v{i}\n"); git("add", "-A"); git("commit", "-qm", f"c{i}")
            made.append(git("rev-parse", "HEAD"))
        self.assertEqual(previews.history(made[-1], cwd=d, main="main"), [made[0], made[2], made[3]])  # notes alone: none, but the head
        for i in range(12):
            (d / "site-src" / "a.css").write_text(f"x{i}\n"); git("commit", "-qam", f"x{i}")
        head = git("rev-parse", "HEAD")
        kept = previews.history(head, cwd=d, main="main")
        self.assertEqual(len(kept), previews.MAX_COMMITS)
        self.assertEqual(kept[-1], head)

    def test_no_merge_base_gives_the_head_alone(self):
        import subprocess
        import tempfile
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        d = pathlib.Path(tmp.name)
        git = lambda *a: subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=d, check=True, capture_output=True, text=True).stdout.strip()
        git("init", "-q", "-b", "main")
        (d / "site-src").mkdir(); (d / "site-src" / "a.css").write_text("0\n"); git("add", "-A"); git("commit", "-qm", "base")
        git("checkout", "-q", "--orphan", "pr"); (d / "site-src" / "a.css").write_text("1\n"); git("add", "-A"); git("commit", "-qm", "alone")
        (d / "site-src" / "a.css").write_text("2\n"); git("commit", "-qam", "again")
        head = git("rev-parse", "HEAD")
        self.assertEqual(previews.history(head, cwd=d, main="main"), [head])  # never the commits of main

    def test_a_merge_of_main_into_the_branch(self):
        import subprocess
        import tempfile
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        d = pathlib.Path(tmp.name)
        git = lambda *a: subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=d, check=True, capture_output=True, text=True).stdout.strip()
        git("init", "-q", "-b", "main")
        (d / "site-src").mkdir(); (d / "data").mkdir()
        (d / "site-src" / "a.css").write_text("0\n"); (d / "data" / "x.toml").write_text("0\n"); git("add", "-A"); git("commit", "-qm", "base")
        git("checkout", "-qb", "pr"); (d / "site-src" / "a.css").write_text("1\n"); git("commit", "-qam", "pr1")
        first = git("rev-parse", "HEAD")
        git("checkout", "-q", "main"); (d / "data" / "x.toml").write_text("main\n"); git("commit", "-qam", "main moved")
        main_commit = git("rev-parse", "HEAD")
        git("checkout", "-q", "pr"); git("merge", "-q", "--no-edit", "main")
        merge = git("rev-parse", "HEAD")
        (d / "site-src" / "a.css").write_text("2\n"); git("commit", "-qam", "pr2")
        head = git("rev-parse", "HEAD")
        kept = previews.history(head, cwd=d, main="main")
        self.assertEqual(kept, [first, merge, head])  # the merge is kept here; its website, the same as before, is folded away after the build
        self.assertNotIn(main_commit, kept)

    def test_digest(self):
        import tempfile
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            for d in (a, b):
                (pathlib.Path(d) / "index.html").write_text("x")
            self.assertEqual(previews.digest(pathlib.Path(a)), previews.digest(pathlib.Path(b)))
            (pathlib.Path(b) / "about.html").write_text("y")
            self.assertNotEqual(previews.digest(pathlib.Path(a)), previews.digest(pathlib.Path(b)))


class Fetch(unittest.TestCase):
    """The merge base found in every situation of the workflow, whole history kept."""
    def setUp(self):
        import subprocess
        import tempfile
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = pathlib.Path(tmp.name)
        up = self.tmp / "up"
        up.mkdir()
        self.git = lambda d, *a: subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=d, check=True, capture_output=True, text=True).stdout.strip()
        git = self.git
        git(up, "init", "-q", "-b", "main"); git(up, "config", "uploadpack.allowReachableSHA1InWant", "true")
        (up / "a").write_text("0\n"); git(up, "add", "-A"); git(up, "commit", "-qm", "base")
        self.prs = []
        for name in ("pr", "pr2"):
            git(up, "checkout", "-q", "-b", name, "main"); (up / name).write_text("x\n"); git(up, "add", "-A"); git(up, "commit", "-qm", name)
            self.prs.append(git(up, "rev-parse", "HEAD"))
        git(up, "checkout", "-q", "main"); (up / "b").write_text("x\n"); git(up, "add", "-A"); git(up, "commit", "-qm", "main moved")
        self.up = up

    def clone(self, *args):
        import subprocess
        ci = self.tmp / f"ci{len(list(self.tmp.iterdir()))}"
        subprocess.run(["git", "clone", "-q", "--depth", "1", "--no-local", *args, str(self.up), str(ci)], check=True, capture_output=True)
        return ci

    def base_found(self, ci, pr):
        import subprocess
        return subprocess.run(["git", "merge-base", "refs/remotes/origin/main", pr], cwd=ci, capture_output=True).returncode == 0

    def test_push_to_main(self):  # the checkout holds main one commit deep
        ci = self.clone("-b", "main")
        previews.fetch(self.prs[0], cwd=ci)
        self.assertTrue(self.base_found(ci, self.prs[0]))

    def test_pull_request(self):  # the checkout holds the branch only, no origin/main yet
        ci = self.clone("-b", "pr", "--single-branch")
        previews.fetch(self.prs[0], cwd=ci)
        self.assertTrue(self.base_found(ci, self.prs[0]))

    def test_two_pull_requests_in_a_row(self):  # the second fetch keeps the whole history
        import subprocess
        ci = self.clone("-b", "main")
        for pr in self.prs:
            previews.fetch(pr, cwd=ci)
            self.assertTrue(self.base_found(ci, pr))
        self.assertEqual(subprocess.run(["git", "rev-parse", "--is-shallow-repository"], cwd=ci, capture_output=True, text=True).stdout.strip(), "false")

class Notes(unittest.TestCase):
    """What to compare: trailers Preview-compare of the branch's commits, for their own commit or an earlier one."""
    def test_notes(self):
        import subprocess
        import tempfile
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        d = pathlib.Path(tmp.name)
        git = lambda *a: subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=d, check=True, capture_output=True, text=True).stdout.strip()
        git("init", "-q", "-b", "main"); (d / "a").write_text("0\n"); git("add", "-A"); git("commit", "-qm", "base")
        git("checkout", "-qb", "pr")
        (d / "a").write_text("1\n"); git("commit", "-qam", "variant A")
        a = git("rev-parse", "HEAD")
        (d / "a").write_text("2\n"); git("commit", "-qam", "variant B\n\nPreview-compare: Variant B, the tiles")
        b = git("rev-parse", "HEAD")
        (d / "a").write_text("3\n"); git("commit", "-qam", f"notes\n\nPreview-compare: {a[:7]} Variant A, the brick\nCo-Authored-By: x <x@x>")
        self.assertEqual(previews.notes(git("rev-parse", "HEAD"), cwd=d, main="main"), {a: "Variant A, the brick", b: "Variant B, the tiles"})
        (d / "a").write_text("4\n"); git("commit", "-qam", "more\n\nPreview-compare: a long note\n  folded on two lines\nPreview-compare: " + b[:7])
        out = previews.notes(git("rev-parse", "HEAD"), cwd=d, main="main")
        self.assertEqual(out[git("rev-parse", "HEAD")], "a long note folded on two lines")  # unfolded
        self.assertEqual(out[b], "to compare")  # marked without a note
        (d / "a").write_text("5\n"); git("commit", "-qam", "defaced\n\nPreview-compare: defaced pages, to look at")
        self.assertEqual(previews.notes(git("rev-parse", "HEAD"), cwd=d, main="main")[git("rev-parse", "HEAD")], "defaced pages, to look at")  # no commit starts so


class Unchanged(unittest.TestCase):
    """A pull request whose website is main's gets no preview, and the workflow reads its number."""
    def test_heads_and_output(self):
        import os
        import tempfile
        saved = {k: getattr(previews, k) for k in ("fetch", "history", "notes", "one", "published")}
        self.addCleanup(lambda: [setattr(previews, k, v) for k, v in saved.items()])
        previews.fetch = lambda sha: None
        previews.history = lambda sha: [sha]
        previews.notes = lambda sha: {}
        previews.one = lambda p, c, dest, listed, env: (dest.mkdir(parents=True, exist_ok=True), {"same": "M", "new": "X"}[p["title"]])[1]
        previews.published = lambda env: "M"
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp)
            same, new = {"n": 63, "sha": "a" * 40, "title": "same", "url": "u"}, {"n": 61, "sha": "b" * 40, "title": "new", "url": "u"}
            self.assertTrue(previews.heads(same, out, {}))
            self.assertTrue(previews.heads(new, out, {}))
            self.assertTrue(same.get("unchanged"))
            self.assertFalse((out / "63").exists())
            self.assertTrue((out / "61").exists() and not new.get("unchanged"))
            f = out / "output"
            previews.unchanged_output([same, new, {"n": "7; echo", "unchanged": False}], f)
            self.assertEqual(f.read_text(), "unchanged=63\n")
            self.assertFalse(os.path.exists(out / "63" / "c"))

    def test_published_once_and_none_when_main_fails(self):
        import subprocess
        saved = previews.site_of, previews.PUBLISHED.copy()
        def restore():
            previews.site_of = saved[0]
            previews.PUBLISHED.clear(); previews.PUBLISHED.update(saved[1])
        self.addCleanup(restore)
        calls = []
        def built(sha, wt, env):
            calls.append(sha)
            (wt / "site").mkdir(parents=True)
            (wt / "site" / "index.html").write_text("main")
            return True, ""
        previews.site_of = built
        previews.PUBLISHED.clear()
        first = previews.published({})
        self.assertEqual(first, previews.published({}))
        self.assertEqual(len(calls), 1)  # once per run
        previews.PUBLISHED.clear()
        def broken(sha, wt, env):
            raise subprocess.CalledProcessError(1, "build")
        previews.site_of = broken
        self.assertIsNone(previews.published({}))  # then every pull request gets its preview


class Fold(unittest.TestCase):
    """Which built commits stay: none the same as the one before; an earlier commit the same as the head goes, the head names it."""
    def rows(self, digests):
        return [{"sha": f"{i}" * 40, "digest": d, "head": i == len(digests) - 1} for i, d in enumerate(digests)]

    def test_same_as_the_commit_before(self):
        kept = previews.fold(self.rows(["a", "a", "b", "c"]))
        self.assertEqual([r["digest"] for r in kept], ["a", "b", "c"])
        self.assertNotIn("made", kept[-1])

    def test_head_same_as_earlier(self):
        kept = previews.fold(self.rows(["a", "b", "b", "b"]))
        self.assertEqual([r["digest"] for r in kept], ["a", "b"])
        self.assertTrue(kept[-1]["head"])
        self.assertEqual(kept[-1]["made"], "1" * 40)  # the first commit of the run of the same website

    def test_a_note_on_a_folded_commit_is_kept(self):
        rows = self.rows(["a", "b", "b", "c", "c"])
        kept = previews.fold(rows)
        self.assertEqual([r["sha"][0] for r in kept], ["0", "1", "4"])
        self.assertEqual(kept[1]["folded"], ["2" * 40])
        self.assertEqual(previews.note_of(kept[1], {"2" * 40: "the note"}), "the note")  # its note on the commit folded away
        self.assertEqual(kept[2]["made"], "3" * 40)
        self.assertEqual(previews.note_of(kept[2], {"4" * 40: "own note of the head"}), "own note of the head")

    def test_head_alone(self):
        kept = previews.fold(self.rows(["a"]))
        self.assertEqual(len(kept), 1)
        self.assertTrue(kept[0]["head"])


class Place(unittest.TestCase):
    """A build copied: its pages marked, no symbolic link published, the earlier commits under c/ left as they are."""
    def test_place(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            site, dest = pathlib.Path(tmp) / "site", pathlib.Path(tmp) / "out" / "61"
            (site / "fr").mkdir(parents=True)
            page = '<!DOCTYPE html><html lang="en"><head><title>t</title></head><body><p>x</p></body></html>'
            (site / "index.html").write_text(page); (site / "fr" / "index.html").write_text(page.replace('"en"', '"fr"'))
            os.symlink("/etc/passwd", site / "leak")
            (dest / "c" / "abc1234").mkdir(parents=True)
            (dest / "c" / "abc1234" / "index.html").write_text("earlier")
            previews.place(site, dest, 61, "d" * 40, "u", True, "4.11", "https://x/preview/61/c/")
            self.assertFalse((dest / "leak").exists() or (dest / "leak").is_symlink())
            for f in ("index.html", "fr/index.html"):
                doc = (dest / f).read_text()
                self.assertEqual(doc.count('role="note"'), 1, f)
                self.assertIn("https://x/preview/61/c/", doc)
            self.assertEqual((dest / "c" / "abc1234" / "index.html").read_text(), "earlier")


class Paths(unittest.TestCase):
    """SITE covers the files that start the Preview workflow (except the workflow and this script, which build nothing)."""
    def test_site_covers_the_workflow_paths(self):
        import re
        flow = (pathlib.Path(__file__).resolve().parent.parent / ".github" / "workflows" / "preview.yml").read_text()
        paths = re.findall(r'"([^"]+)"', re.search(r"paths: \[(.*?)\]", flow).group(1))
        for path in paths:
            if path.startswith("!") or path in ("scripts/previews.py", "scripts/compare.html", ".github/workflows/preview.yml"):
                continue
            self.assertTrue(path.rstrip("*").startswith(previews.SITE), path)


if __name__ == "__main__":
    unittest.main()
