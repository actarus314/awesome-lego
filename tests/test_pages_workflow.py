"""The Pages workflow publishes the newest previews built (.github/workflows/pages.yml)."""
import unittest
from pathlib import Path

PAGES = (Path(__file__).resolve().parent.parent / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")


class Previews(unittest.TestCase):
    def test_the_newest_artefact_by_its_date(self):
        # the API does not list the artefacts newest first: a closed pull request kept its preview (27/11/2026)
        line = next(x for x in PAGES.splitlines() if "artifacts?name=previews" in x)
        self.assertIn("sort_by(.created_at) | last", line)
        self.assertIn("head_repository_id", line)   # never a fork's


if __name__ == "__main__":
    unittest.main()
