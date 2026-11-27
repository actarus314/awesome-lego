"""Runs that wait (MAINTENANCE.md, Workflows in detail): on main, nothing is cancelled."""
import re
import unittest
from pathlib import Path

WORKFLOWS = Path(__file__).resolve().parent.parent / ".github" / "workflows"


def text(name):
    return (WORKFLOWS / name).read_text(encoding="utf-8")


class Concurrency(unittest.TestCase):
    def test_runs_on_main_queue_and_none_is_dropped(self):
        # a dropped run of Release leaves a version without its tag; of Pages, a day without measurements (27/11/2026)
        for name in ("version.yml", "release.yml", "pages.yml", "preview.yml"):
            group = re.search(r"(?m)^( *)concurrency:\n((?:\1  .*\n)+)", text(name)).group(2)
            self.assertRegex(group, r"\bqueue: max\b", name)
            self.assertNotIn("cancel-in-progress: true", group, name)

    def test_a_pull_request_cancels_its_previous_run_main_keeps_each(self):
        for name in ("check.yml", "zizmor.yml", "render.yml"):
            self.assertIn("github.event_name == 'pull_request' && github.ref || github.sha", text(name), name)
            self.assertIn("cancel-in-progress: ${{ github.event_name == 'pull_request' }}", text(name), name)

    def test_a_merged_pull_request_is_not_rebuilt_twice(self):
        self.assertIn("!github.event.pull_request.merged", text("preview.yml"))


if __name__ == "__main__":
    unittest.main()
