"""Fragments of changes/ and the assembly of the next version (scripts/changes.py, workflows Check and Version);
generated files left to Version while a fragment waits (scripts/build.py). Each check fails on a planted defect."""
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import autofix  # noqa: E402
import build  # noqa: E402
import changes  # noqa: E402

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
               "odd-type.md": "type: patch\n\nText.\n",
               "no-blank.md": "type: minor\nText.\n",
               "empty.md": "type: minor\n\n",
               "two-paragraphs.md": "type: minor\n\nOne.\n\nTwo.\n",
               "heading.md": "type: minor\n\n## v9.9 — 2026-01-01\n",
               "too-long.md": "type: minor\n\n" + "x" * (build.CHANGELOG_MAX + 1) + "\n",
               "major-alone.md": "type: major\n\nData: new format.\n",
               "minor-series.md": "type: minor\nseries: A series.\n\nText.\n",
               "notes.txt": "type: none\n\nText.\n"}
        found, errors = changes.fragments(self.write(bad))
        self.assertEqual(found, [])
        self.assertEqual(sorted(e.split(":")[0] for e in errors), sorted(f"changes/{n}" for n in bad))

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

    def test_strict_refuses_a_minor_fragment_left(self):
        self.assertEqual(self.run_in({"site.md": "type: minor\n\nWebsite: two.\n"}, "check", "--strict")[0], 1)
        self.assertEqual(self.run_in({"tidy.md": "type: none\n\nAutomation: one.\n"}, "check", "--strict")[0], 0)
        self.assertEqual(self.run_in({"site.md": "type: minor\n\nWebsite: two.\n"}, "check")[0], 0)


class PullRequest(unittest.TestCase):
    def test_files_left_to_version_are_refused(self):
        for f in changes.LEFT_TO_VERSION:
            errors, _ = changes.pull_request({f, "data/shops.toml"}, CHANGELOG, CHANGELOG, True)
            self.assertEqual(len(errors), 1, f)
        self.assertIn("media/site-preview.png", changes.LEFT_TO_VERSION)

    def test_a_new_changelog_section_is_refused_an_old_one_reworded_is_not(self):
        added = CHANGELOG.replace("## v4.4", "## v4.5 — 2026-12-01\nNew.\n\n## v4.4")
        self.assertEqual(len(changes.pull_request({"CHANGELOG.md"}, CHANGELOG, added, True)[0]), 1)
        self.assertEqual(changes.pull_request({"CHANGELOG.md"}, CHANGELOG, CHANGELOG.replace("four four", "four, four"), False), ([], []))

    def test_content_without_a_fragment_is_warned(self):
        self.assertEqual(len(changes.pull_request({"data/shops.toml"}, CHANGELOG, CHANGELOG, False)[1]), 1)
        self.assertEqual(len(changes.pull_request({"site-src/app.js"}, CHANGELOG, CHANGELOG, False)[1]), 1)
        self.assertEqual(changes.pull_request({"data/shops.toml", "changes/x.md"}, CHANGELOG, CHANGELOG, True), ([], []))
        self.assertEqual(changes.pull_request({"scripts/tidy.py"}, CHANGELOG, CHANGELOG, False), ([], []))


class GeneratedFiles(unittest.TestCase):
    def test_left_to_version_while_a_fragment_waits(self):
        self.assertEqual(build.out_of_date([], [], False), ([], []))
        errors, warnings = build.out_of_date(["README.md"], [Path("changes/a.md")], False)
        self.assertEqual((errors, len(warnings)), ([], 1))

    def test_an_error_without_fragment_or_on_the_pull_request_of_version(self):
        self.assertEqual(len(build.out_of_date(["README.md"], [], False)[0]), 1)
        self.assertEqual(len(build.out_of_date(["README.md", "full-list.md"], [Path("changes/a.md")], True)[0]), 2)


class DataFixes(unittest.TestCase):
    def test_the_fragment_of_data_fixes_is_well_formed(self):
        for moved, past, text in ((1, 0, "Data fixes: 1 address moved for good."), (3, 2, "Data fixes: 3 addresses moved for good and 2 past event dates removed."),
                                  (0, 1, "Data fixes: 1 past event date removed.")):
            self.assertEqual(autofix.fragment(moved, past), text)
            with tempfile.TemporaryDirectory() as d:
                p = Path(d) / f"data-fixes-{autofix.TODAY}.md"
                p.write_text(f"type: none\n\n{text}\n", encoding="utf-8")
                self.assertEqual(changes.parse(p), ("none", "", text))


if __name__ == "__main__":
    unittest.main()
