import datetime as dt
import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
import links_issue  # noqa: E402
import refresh  # noqa: E402

T = refresh.TODAY
iso = lambda n: (T - dt.timedelta(days=n)).isoformat()


class Selection(unittest.TestCase):
    def test_rank_one_international(self):
        self.assertFalse(refresh.selected({"featured": True}))
        self.assertFalse(refresh.selected({}))
        self.assertTrue(refresh.selected({"rank": {"intl": 1}}))
        self.assertFalse(refresh.selected({"rank": {"intl": 2, "FR": 1}}))


class Month(unittest.TestCase):
    def test_changes_of_the_month(self):
        days = {iso(40): {"a": {"last_activity": iso(170)}, "b": {"archived": False}, "gone": {}},
                iso(31): {"a": {"last_activity": iso(170)}, "b": {"archived": False}, "gone": {}, "removed": {}},
                iso(0): {"a": {"last_activity": iso(201)}, "b": {"archived": True}, "c": {}}}
        head, items = refresh.month_changes(days, {"a", "b", "c", "gone"})
        self.assertIn(f"From {refresh.date_en(iso(31))} to {refresh.date_en(iso(0))}; 3 days kept", head)
        text = "\n".join(items)
        self.assertIn("a: active → slow", text)
        self.assertIn("1 day kept", refresh.month_changes({iso(0): {}}, set())[0])
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
        month = (T.replace(day=1) - dt.timedelta(days=1)).isoformat()[:7]   # last month
        previous = ('Monthly data report: 4 November 2026. Read by the monthly review.\n<!-- report-ids '
                    + json.dumps({"month": month, "date": "4 November 2026", "ids": {"read failures": ["a", "b"], "archived": []}}) + " -->")
        when, kept, base = refresh.guard(previous, {"read failures": ["b", "c"], "archived": ["d"]})
        self.assertEqual(when, "4 November 2026")
        self.assertEqual(kept, {"read failures": ["b"]})
        self.assertEqual(refresh.guard("", {"read failures": ["b"]}), (None, {}, {}))
        # written again the same month: compared with last month's report, not with itself
        again = "<!-- report-ids " + json.dumps({"month": T.isoformat()[:7], "date": refresh.date_en(T), "ids": {"read failures": ["b", "c"]}, "base": base}) + " -->"
        self.assertEqual(refresh.guard(again, {"read failures": ["b", "c"]})[:2], ("4 November 2026", {"read failures": ["b"]}))

    def test_history_that_cannot_be_read(self):
        self.assertEqual(refresh.month_changes(None, set()), ("The `history` branch could not be read this month.", []))
        self.assertIsNone(refresh.archived_since(None, "x"))

    def test_links_that_block_github_come_from_the_links_issue(self):
        report = "### Errors in data/brands.toml\n\n* [503] <https://a.example/> (at 3:8) | Rejected status code: 503\n"
        text, _ = links_issue.body(report, rechecked={"https://a.example/": ("alive", ["200, 200, 200"], None)}, today=dt.date(2026, 11, 25))
        title, lines = refresh.links_blocking(text)
        self.assertEqual(title, "They block GitHub, alive according to Globalping on 25 November 2026 (1)")
        self.assertEqual(len(lines), 1)
        self.assertIn("<https://a.example/>", lines[0])
        self.assertEqual(refresh.links_blocking("Every link answers."), (None, []))


class Command(unittest.TestCase):
    def test_main_with_read_failures(self):
        """The whole script, as Pages and the Data report run it, with entries that fail to be read."""
        import contextlib
        import io
        import json as j
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as d:
            out = pathlib.Path(d) / "metrics.json"
            ids = []
            for path in sorted((refresh.ROOT / "data").glob("*.toml")):
                ids += [r["id"] for r in refresh.tomllib.loads(path.read_text(encoding="utf-8")).get("resource", [])]
            out.write_text(j.dumps({i: {"refreshed": iso(10), "last_activity": iso(400), "archived": True} for i in ids[:5]}), encoding="utf-8")
            fail = lambda r, old, token: (dict(old.get(r["id"], {})) or None, f"{r['id']}: HTTPError") if r["id"] in ids[:5] else (None, None)
            for argv in (["refresh.py"], ["refresh.py", "--month"]):
                buf = io.StringIO()
                with mock.patch.object(refresh, "OUT", out), mock.patch.object(refresh, "site_metrics", return_value=None), \
                     mock.patch.object(refresh, "read", fail), mock.patch.object(refresh.trends, "snapshots", return_value={}), \
                     mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(buf):
                    self.assertEqual(refresh.main(), 0)
                text = buf.getvalue()
                self.assertIn(f"{ids[0]}: HTTPError (last read {refresh.date_en(iso(10))}, 10 days ago)", text)
                self.assertNotRegex(text.split("<!--")[0], r"\(\d{4}-\d{2}-\d{2}\)")   # dates in letters
            self.assertIn("Monthly data report:", text)
            self.assertIn("report-ids", text)


if __name__ == "__main__":
    unittest.main()
