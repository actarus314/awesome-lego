"""The notes of the GitHub releases follow CHANGELOG.md (scripts/release_notes.py, workflow Release)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import release_notes  # noqa: E402

LOG = "# Changelog\n\nIntro.\n\n# v2.x — series\n\n## v2.1 — 2026-01-02\nShort entry.\n\n## v2.0 — 2026-01-01\nFirst line.\nSecond line.\n\n# v1.x — older\n\n## v1.0 — 2025-12-01\nOld.\n"


class Section(unittest.TestCase):
    def test_a_section_stops_at_the_next_version_or_series(self):
        self.assertEqual(release_notes.section(LOG, "v2.0"), "First line.\nSecond line.")
        self.assertEqual(release_notes.section(LOG, "v1.0"), "Old.")
        self.assertEqual(release_notes.section(LOG, "v2.10"), "")  # v2.1 is not a prefix of v2.10

    def test_every_version_of_the_repository_has_its_section(self):
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        version = "v" + (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.assertTrue(release_notes.section(text, version))


class Stale(unittest.TestCase):
    def test_only_releases_whose_notes_differ_are_rewritten(self):
        releases = [{"tag_name": "v2.1", "body": "Short entry.\n"}, {"tag_name": "v2.0", "body": "A long old note."},
                    {"tag_name": "v0.9", "body": "No section: kept."}]
        self.assertEqual(release_notes.stale(releases, LOG), [("v2.0", "First line.\nSecond line.")])


if __name__ == "__main__":
    unittest.main()
