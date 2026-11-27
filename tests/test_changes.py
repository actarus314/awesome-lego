"""Fragments of changes/ and the assembly of the next version (scripts/changes.py, workflows Check and Version);
generated files left to Version while a fragment waits (scripts/build.py). Each check fails on a planted defect."""
import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build  # noqa: E402
import changes  # noqa: E402

FORM = """name: Add a resource
body:
  - type: dropdown
    attributes:
      label: Category
      options:
        - Brands
        - Shops
"""

CHANGELOG = """# Changelog

# v4.x — Series four.

## v4.4 — 2026-11-26
Website: four four.

# v3.x — Series three.
"""


class Fragments(unittest.TestCase):
    def write(self, files):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        d = Path(tmp.name)
        for name, text in files.items():
            (d / name).write_text(text, encoding="utf-8")
        return d

    def test_well_formed_fragments_are_read_strongest_first(self):
        found, errors = changes.fragments(self.write({"a-tidy.md": "type: none\n\nAutomation: one.\n",
                                                      "b-site.md": "type: minor\n\nWebsite: two,\nwrapped.\n"}))
        self.assertEqual(errors, [])
        self.assertEqual([(f[0].name, f[1], f[3]) for f in found], [("b-site.md", "minor", "Website: two, wrapped."), ("a-tidy.md", "none", "Automation: one.")])

    def test_defects_are_refused(self):
        bad = {"Bad_Name.md": "type: minor\n\nText.\n",
               "no-type.md": "Website: text.\n",
               "odd-type.md": "type: fix\n\nText.\n",
               "no-blank.md": "type: minor\nText.\n",
               "empty.md": "type: minor\n\n",
               "two-paragraphs.md": "type: minor\n\nOne.\n\nTwo.\n",
               "heading.md": "type: minor\n\n## v9.9 — 2026-01-01\n",
               "too-long.md": "type: minor\n\n" + "x" * (build.CHANGELOG_MAX + 1) + "\n",
               "major-alone.md": "type: major\n\nData: new format.\n",
               "minor-series.md": "type: minor\nseries: A series.\n\nText.\n",
               "notes.txt": "type: none\n\nText.\n",
               "empty-series.md": "type: minor\nseries:\n\nText.\n",
               "mention.md": "type: minor\n\nWebsite: thanks to @someone for the report.\n",
               "html.md": "type: minor\n\nWebsite: a <script> in the text.\n"}
        found, errors = changes.fragments(self.write(bad))
        self.assertEqual(found, [])
        self.assertEqual(sorted(e.split(":")[0] for e in errors), sorted(f"changes/{n}" for n in bad))

    def test_a_folder_named_like_a_fragment_is_refused(self):
        d = self.write({})
        (d / "x.md").mkdir()
        self.assertEqual(changes.fragments(d), ([], ["changes/x.md: a fragment is a file, not a folder"]))

    def test_a_byte_order_mark_and_a_mention_in_backticks_pass(self):
        found, errors = changes.fragments(self.write({"bom.md": "\ufefftype: minor\n\nAutomation: the `@types/node` package, `changes/<name>.md`, and a@b.example.\n"}))
        self.assertEqual((errors, found[0][1]), ([], "minor"))

    def test_two_major_fragments_are_refused(self):
        found, errors = changes.fragments(self.write({"a.md": "type: major\nseries: One.\n\nData: one.\n", "b.md": "type: major\nseries: Two.\n\nData: two.\n"}))
        self.assertEqual(len(found), 2)
        self.assertEqual(len(errors), 1)
        self.assertIn("2 major fragments", errors[0])

    def test_the_longest_fragment_allowed_passes(self):
        found, errors = changes.fragments(self.write({"long.md": "type: minor\n\n" + "x" * build.CHANGELOG_MAX + "\n"}))
        self.assertEqual((len(found), errors), (1, []))


class Assemble(unittest.TestCase):
    def frag(self, name, kind, text, series=""):
        return (Path(name), kind, series, text)

    def test_minor_raises_the_minor_and_cites_the_fragments_of_type_none(self):
        new, text = changes.assemble([self.frag("b.md", "minor", "Website: two."), self.frag("a.md", "none", "Automation: one.")], "4.4", CHANGELOG, "2026-12-01")
        self.assertEqual(new, "4.5")
        self.assertIn("# v4.x — Series four.\n\n## v4.5 — 2026-12-01\nWebsite: two.\n\nAutomation: one.\n\n## v4.4 — 2026-11-26\n", text)
        self.assertEqual(build.changelog_long(text), [])

    def test_major_opens_a_series(self):
        new, text = changes.assemble([self.frag("a.md", "major", "Data: new format.", "Series five."), self.frag("b.md", "minor", "Website: two.")], "4.4", CHANGELOG, "2026-12-01")
        self.assertEqual(new, "5.0")
        self.assertIn("# Changelog\n\n# v5.x — Series five.\n\n## v5.0 — 2026-12-01\nData: new format.\n\nWebsite: two.\n\n# v4.x — Series four.\n", text)

    def test_patch_raises_the_third_number_shown_only_when_not_zero(self):
        new, text = changes.assemble([self.frag("fix.md", "patch", "Data: two addresses moved.")], "4.4", CHANGELOG, "2026-12-01")
        self.assertEqual(new, "4.4.1")
        self.assertIn("# v4.x — Series four.\n\n## v4.4.1 — 2026-12-01\nData: two addresses moved.\n\n## v4.4 — 2026-11-26\n", text)
        self.assertEqual(changes.bump("4.4.1", {"patch"}), "4.4.2")
        self.assertEqual(changes.bump("4.4.2", {"minor", "patch"}), "4.5")
        self.assertEqual(changes.bump("4.4.2", {"major"}), "5.0")
        self.assertEqual(changes.bump("4.4.2", {"none"}), None)

    def test_a_version_of_another_shape_is_refused(self):
        for bad in ("4", "4.4.1.1", "v4.4"):
            with self.assertRaises((SystemExit, ValueError)):
                changes.bump(bad, {"patch"})

    def test_a_website_change_without_fragment_gives_a_patch(self):
        new, text = changes.assemble([self.frag("a.md", "none", "Automation: one.")], "4.4", CHANGELOG, "2026-12-01", site_changed=True)
        self.assertEqual(new, "4.4.1")
        self.assertIn("## v4.4.1 — 2026-12-01\n" + changes.SITE_ONLY + "\n\nAutomation: one.\n", text)
        new, _ = changes.assemble([self.frag("b.md", "minor", "Website: two.")], "4.4", CHANGELOG, "2026-12-01", site_changed=True)
        self.assertEqual(new, "4.5")
        self.assertEqual(changes.assemble([], "4.4", CHANGELOG, "2026-12-01"), (None, CHANGELOG))

    def test_the_readers_of_the_changelog_see_three_numbers(self):
        text = "## v4.4.1 — 2026-12-01\n" + "x" * (build.CHANGELOG_MAX + 1) + "\n"
        self.assertEqual(build.changelog_long(text), [f"v4.4.1: {build.CHANGELOG_MAX + 1} characters"])
        self.assertEqual(changes.sections(text + "## v4.4 — 2026-11-26\nOne.\n"), {"4.4.1", "4.4"})

    def test_fragments_of_type_none_wait(self):
        self.assertEqual(changes.assemble([self.frag("a.md", "none", "Automation: one.")], "4.4", CHANGELOG, "2026-12-01"), (None, CHANGELOG))
        self.assertEqual(changes.assemble([], "4.4", CHANGELOG, "2026-12-01"), (None, CHANGELOG))

    def test_each_paragraph_of_an_entry_is_held_to_the_limit(self):
        text = "## v9.1 — 2026-01-01\n" + "x" * build.CHANGELOG_MAX + "\n\n" + "y" * build.CHANGELOG_MAX + "\n\n" + "z" * (build.CHANGELOG_MAX + 1) + "\n"
        self.assertEqual(build.changelog_long(text), [f"v9.1: {build.CHANGELOG_MAX + 1} characters"])


class Command(unittest.TestCase):
    """`assemble` on a copy of VERSION, CHANGELOG.md and changes/, as the workflow Version runs it."""
    def run_in(self, files, *argv):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "changes").mkdir()
        (root / "VERSION").write_text("4.4\n", encoding="utf-8")
        (root / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")
        for name, text in files.items():
            (root / "changes" / name).write_text(text, encoding="utf-8")
        old, changes.ROOT = changes.ROOT, root
        try:
            out = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                code = changes.main(list(argv))
        finally:
            changes.ROOT = old
        return code, out.getvalue(), root

    def test_assemble_writes_the_version_and_removes_the_fragments(self):
        code, out, root = self.run_in({"site.md": "type: minor\n\nWebsite: two.\n", "tidy.md": "type: none\n\nAutomation: one.\n"}, "assemble", "--date", "2026-12-01")
        self.assertEqual((code, out), (0, "version=4.5\n"))
        self.assertEqual((root / "VERSION").read_text(encoding="utf-8"), "4.5\n")
        self.assertIn("## v4.5 — 2026-12-01\nWebsite: two.\n\nAutomation: one.\n", (root / "CHANGELOG.md").read_text(encoding="utf-8"))
        self.assertEqual(list((root / "changes").iterdir()), [])

    def test_assemble_leaves_everything_when_every_fragment_is_of_type_none(self):
        code, out, root = self.run_in({"tidy.md": "type: none\n\nAutomation: one.\n"}, "assemble")
        self.assertEqual((code, out, (root / "VERSION").read_text(encoding="utf-8")), (0, "", "4.4\n"))
        self.assertEqual([p.name for p in (root / "changes").iterdir()], ["tidy.md"])

    def test_a_defect_stops_assemble_and_check(self):
        for argv in (["assemble"], ["check"]):
            code, _, root = self.run_in({"bad.md": "Website: no type.\n"}, *argv)
            self.assertEqual(code, 1, argv)
            self.assertEqual((root / "VERSION").read_text(encoding="utf-8"), "4.4\n")

    def test_next_says_the_number_a_merge_would_give(self):
        self.assertEqual(self.run_in({"fix.md": "type: patch\n\nData: one.\n"}, "next")[:2], (0, "4.4.1\n"))
        self.assertEqual(self.run_in({"site.md": "type: minor\n\nWebsite: two.\n", "fix.md": "type: patch\n\nData: one.\n"}, "next")[:2], (0, "4.5\n"))
        self.assertEqual(self.run_in({"tidy.md": "type: none\n\nAutomation: one.\n"}, "next")[:2], (0, ""))
        self.assertEqual(self.run_in({}, "next", "--types", "minor,none")[:2], (0, "4.5\n"))
        self.assertEqual(self.run_in({}, "next", "--types", "fix")[0], 1)

    def test_next_gives_a_patch_for_a_website_change_without_fragment(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        served, tools = Path(tmp.name) / "served.txt", Path(tmp.name) / "tools.txt"
        served.write_text("site-src/vendor/minisearch.min.js\n.github/workflows/check.yml\n", encoding="utf-8")
        tools.write_text(".github/workflows/check.yml\nmedia/site-preview.png\npackage-lock.json\ndev/registre.md\n", encoding="utf-8")
        self.assertEqual(self.run_in({}, "next", "--types", "", "--changed", str(served))[:2], (0, "4.4.1\n"))
        self.assertEqual(self.run_in({}, "next", "--types", "none", "--changed", str(tools))[:2], (0, ""))
        self.assertEqual(self.run_in({}, "next", "--types", "minor", "--changed", str(served))[:2], (0, "4.5\n"))

    def test_what_the_website_serves(self):
        self.assertTrue(changes.site_changed(["data/shops.toml"]))
        self.assertTrue(changes.site_changed(["site-src/app.js", "dev/x.md"]))
        self.assertTrue(changes.site_changed(["scripts/build.py"]))
        self.assertFalse(changes.site_changed(["media/site-preview.png", "media/site-preview-dark.png", "README.md", "scripts/check_site.py", ".github/workflows/pages.yml"]))


class PullRequest(unittest.TestCase):
    def texts(self, changelog=CHANGELOG, form=FORM):
        return {"CHANGELOG.md": changelog, changes.FORM: form}

    def test_files_left_to_version_are_refused(self):
        for f in changes.LEFT_TO_VERSION:
            errors, _ = changes.pull_request({f, "data/shops.toml"}, self.texts(), self.texts(), True)
            self.assertEqual(len(errors), 1, f)
        self.assertIn("media/site-preview.png", changes.LEFT_TO_VERSION)

    def test_a_new_changelog_section_is_refused_an_old_one_reworded_is_not(self):
        added = CHANGELOG.replace("## v4.4", "## v4.5 — 2026-12-01\nNew.\n\n## v4.4")
        self.assertEqual(len(changes.pull_request({"CHANGELOG.md"}, self.texts(), self.texts(added), True)[0]), 1)
        self.assertEqual(changes.pull_request({"CHANGELOG.md"}, self.texts(), self.texts(CHANGELOG.replace("four four", "four, four")), False), ([], []))

    def test_the_category_list_of_the_form_is_left_to_version_the_rest_is_not(self):
        more = FORM.replace("        - Shops\n", "        - Shops\n        - Videos\n")
        self.assertEqual(len(changes.pull_request({changes.FORM, "changes/x.md", "data/video.toml"}, self.texts(), self.texts(form=more), True)[0]), 1)
        self.assertEqual(changes.pull_request({changes.FORM}, self.texts(), self.texts(form=FORM.replace("Add a resource", "Suggest a resource")), False), ([], []))
        self.assertEqual(changes.categories(FORM), "        - Brands\n        - Shops\n")

    def test_content_without_a_fragment_fails_except_for_renovate(self):
        for f in ("data/shops.toml", "data/backend/population.json", "site-src/app.js"):
            self.assertEqual(len(changes.pull_request({f}, self.texts(), self.texts(), False)[0]), 1, f)
            self.assertEqual(len(changes.pull_request({f}, self.texts(), self.texts(), False, "fix/" + f)[0]), 1, f)
        errors, warnings = changes.pull_request({"site-src/vendor/minisearch.min.js"}, self.texts(), self.texts(), False, "renovate/minisearch-7.x")
        self.assertEqual((errors, len(warnings)), ([], 1))
        self.assertEqual(changes.pull_request({"data/shops.toml", "changes/x.md"}, self.texts(), self.texts(), True), ([], []))
        self.assertEqual(changes.pull_request({"scripts/tidy.py", "media/logos/x.png"}, self.texts(), self.texts(), False, "auto/tidy"), ([], []))


class Git(unittest.TestCase):
    """`check --base` and the files of Version in a scratch git repository, as Check and the workflow run them."""
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.git("init", "-q", "-b", "main")
        for name in ("VERSION", "CHANGELOG.md", "README.md", changes.FORM, "data/shops.toml", "scripts/version_files.sh", "scripts/changes.py", ".github/workflows/check.yml"):
            (self.root / name).parent.mkdir(parents=True, exist_ok=True)
            (self.root / name).write_bytes((ROOT / name).read_bytes())
        self.commit("main")

    def git(self, *args):
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        return subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True, env=env)

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-qm", message)

    def check(self, *argv):
        old, changes.ROOT = changes.ROOT, self.root
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err:
                return changes.main(["check", *argv]), err.getvalue()
        finally:
            changes.ROOT = old

    def test_what_main_changed_since_the_branch_is_not_the_branch_s(self):
        self.git("checkout", "-q", "-b", "topic")
        (self.root / "changes").mkdir()
        (self.root / "changes" / "topic.md").write_text("type: minor\n\nData: one.\n", encoding="utf-8")
        (self.root / "data/shops.toml").write_text("# edited\n", encoding="utf-8")
        self.commit("topic")
        self.git("checkout", "-q", "main")
        (self.root / "VERSION").write_text("0.1\n", encoding="utf-8")  # a version merged on main after the branch left it (0.x: never the version of the repository, which the copy starts from)
        self.commit("v4.5")
        self.git("checkout", "-q", "topic")
        self.assertEqual(self.check("--base", "main"), (0, ""))
        (self.root / "VERSION").write_text("0.2\n", encoding="utf-8")  # the branch itself changes VERSION: refused
        self.commit("bump")
        code, err = self.check("--base", "main")
        self.assertEqual(code, 1)
        self.assertIn("VERSION is written by the Version workflow", err)

    def test_a_branch_without_fragment_that_changes_data_fails(self):
        self.git("checkout", "-q", "-b", "topic")
        (self.root / "data/shops.toml").write_text("# edited\n", encoding="utf-8")
        self.commit("topic")
        self.assertEqual(self.check("--base", "main")[0], 1)
        self.assertEqual(self.check("--base", "main", "--branch", "renovate/x")[0], 0)

    def files(self, *argv):
        """The check of the repository itself (never the copy in the scratch tree, which a patch could rewrite)."""
        return subprocess.run(["bash", str(ROOT / "scripts" / "version_files.sh"), *(argv or ["staged"])], cwd=self.root, capture_output=True, text=True)

    def patch(self, edit, *diff):
        """The patch of `edit` as the build job of Version writes it, then the tree back as it was."""
        edit(self.root)
        self.git("add", "-A")
        text = self.git("diff", "--cached", "--binary", *(diff or ["--no-renames"])).stdout
        staged = self.files("staged").returncode
        self.git("reset", "-q", "--hard")
        self.git("clean", "-qfd")
        f = self.root.parent / (self.root.name + ".patch")
        f.write_text(text, encoding="utf-8")
        self.addCleanup(f.unlink, missing_ok=True)
        return self.files("patch", str(f)).returncode, staged

    def test_a_patch_of_version_passes(self):
        def edit(r):
            (r / "VERSION").write_text("4.5\n", encoding="utf-8")
            (r / "changes").mkdir()
            (r / "changes" / "new.md").write_text("type: none\n\nAutomation: one.\n", encoding="utf-8")
            (r / changes.FORM).write_text("rebuilt\n", encoding="utf-8")
        self.assertEqual(self.patch(edit), (0, 0))

    def test_a_patch_that_writes_elsewhere_is_refused_before_it_is_applied(self):
        def check_script(r):
            (r / "scripts/version_files.sh").write_text("echo $GH_TOKEN\n", encoding="utf-8")
        def workflow(r):
            (r / ".github/workflows/check.yml").write_text("on: push\n", encoding="utf-8")
        def moved(r):
            (r / "changes").mkdir()
            (r / "scripts/changes.py").rename(r / "changes" / "x.md")
        def link(r):
            (r / "changes").mkdir()
            (r / "changes" / "x.md").symlink_to("/etc/passwd")
        def executable(r):
            (r / "README.md").chmod(0o755)
        def odd_name(r):
            (r / "changes").mkdir()
            (r / "changes" / "X.sh").write_text("x\n", encoding="utf-8")
        for edit in (check_script, workflow, moved, link, executable, odd_name):
            self.assertEqual(self.patch(edit), (1, 1), edit.__name__)
        self.assertEqual(self.patch(moved, "-M")[0], 1)  # a patch written with renames is refused too

    def test_the_files_of_version_without_a_folder_changes(self):
        # the usual state after a version: changes/ is gone (git keeps no empty folder); Version started by hand stages with `git add -A`
        self.assertFalse((self.root / "changes").exists())
        (self.root / "README.md").write_text("rebuilt\n", encoding="utf-8")
        self.git("add", "-A")
        self.assertEqual(self.files().returncode, 0)
        (self.root / "data/shops.toml").write_text("# not written by Version\n", encoding="utf-8")
        self.git("add", "-A")
        r = self.files()
        self.assertEqual(r.returncode, 1)
        self.assertIn("data/shops.toml", r.stdout)


class GeneratedFiles(unittest.TestCase):
    def test_left_to_version_while_a_fragment_waits(self):
        self.assertEqual(build.out_of_date([], [], ""), ([], []))
        errors, warnings = build.out_of_date(["README.md"], ["minor"], "")
        self.assertEqual(errors, [])
        self.assertIn("right after the merge", warnings[0])

    def test_the_message_says_when_only_fragments_of_type_none_wait(self):
        errors, warnings = build.out_of_date(["README.md"], ["none"], "")
        self.assertEqual(errors, [])
        self.assertIn("only fragments of type none wait", warnings[0])

    def test_a_pull_request_is_warned_whatever_main_holds(self):
        for waiting in ([], ["none"], ["minor"]):
            errors, warnings = build.out_of_date(["README.md"], waiting, "pull-request")
            self.assertEqual((errors, len(warnings)), ([], 1), waiting)

    def test_an_error_without_fragment_on_main(self):
        self.assertEqual(len(build.out_of_date(["README.md"], [], "")[0]), 1)
        self.assertEqual(len(build.out_of_date(["README.md", "full-list.md"], ["patch"], "")[0]), 0)


if __name__ == "__main__":
    unittest.main()
