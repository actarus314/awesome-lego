import datetime as dt
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
import links_issue  # noqa: E402
import refresh  # noqa: E402

T = refresh.TODAY
iso = lambda n: (T - dt.timedelta(days=n)).isoformat()


class Selection(unittest.TestCase):
    def test_featured_until_ranks_then_rank_one_international(self):
        self.assertTrue(refresh.selected({"featured": True}))
        self.assertFalse(refresh.selected({}))
        self.assertTrue(refresh.selected({"featured": False, "rank": {"intl": 1}}))
        self.assertFalse(refresh.selected({"featured": True, "rank": {"intl": 2, "FR": 1}}))


class Month(unittest.TestCase):
    def test_changes_of_the_month(self):
        days = {iso(40): {"a": {"last_activity": iso(170)}, "b": {"archived": False}, "gone": {}},
                iso(31): {"a": {"last_activity": iso(170)}, "b": {"archived": False}, "gone": {}, "removed": {}},
                iso(0): {"a": {"last_activity": iso(201)}, "b": {"archived": True}, "c": {}}}
        head, items = refresh.month_changes(days, {"a", "b", "c", "gone"})
        self.assertIn(f"From {refresh.date_en(iso(31))} to {refresh.date_en(iso(0))}; 3 days kept", head)
        text = "\n".join(items)
        self.assertIn("a: active → slow", text)
        self.assertIn("Archived on GitHub during the month: b", text)
        self.assertIn("Measured for the first time: c", text)
        self.assertIn("still in the data: gone", text)   # "removed" left the data: not listed
        self.assertNotIn("removed", text)

    def test_empty_history(self):
        self.assertEqual(refresh.month_changes({}, set())[1], [])

    def test_archived_since(self):
        days = {iso(9): {"x": {"archived": True}}, iso(5): {"x": {"archived": False}}, iso(3): {"x": {"archived": True}}, iso(0): {"x": {"archived": True}}}
        self.assertEqual(refresh.archived_since(days, "x"), refresh.since(iso(3)))
        self.assertTrue(refresh.archived_since({iso(2): {"x": {"archived": True}}}, "x").startswith("at least since"))
        self.assertIsNone(refresh.archived_since(days, "y"))

    def test_guard(self):
        previous = 'Monthly data report: 4 November 2026. Read by the monthly review.\n<!-- report-ids {"read failures": ["a", "b"], "archived": []} -->'
        when, kept = refresh.guard(previous, {"read failures": ["b", "c"], "archived": ["d"]})
        self.assertEqual(when, "4 November 2026")
        self.assertEqual(kept, {"read failures": ["b"]})
        self.assertEqual(refresh.guard("", {"read failures": ["b"]}), (None, {}))

    def test_links_that_block_github_come_from_the_links_issue(self):
        report = "### Errors in data/brands.toml\n\n* [503] <https://a.example/> (at 3:8) | Rejected status code: 503\n"
        text, _ = links_issue.body(report, rechecked={"https://a.example/": ("alive", ["200"] * 3, None)}, today=dt.date(2026, 11, 25))
        title, lines = refresh.links_blocking(text)
        self.assertEqual(title, "They block GitHub, alive according to Globalping on 25 November 2026 (1)")
        self.assertEqual(len(lines), 1)
        self.assertIn("<https://a.example/>", lines[0])
        self.assertEqual(refresh.links_blocking("Every link answers."), (None, []))


if __name__ == "__main__":
    unittest.main()
