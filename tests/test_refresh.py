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
    def test_rank_one_international(self):  # the rule of scripts/build.py, which the reports use too
        self.assertFalse(refresh.build.picked({"featured": True}))
        self.assertFalse(refresh.build.picked({}))
        self.assertTrue(refresh.build.picked({"rank": {"intl": 1}}))
        self.assertFalse(refresh.build.picked({"rank": {"intl": 2, "FR": 1}}))


class Cut(unittest.TestCase):
    def test_a_long_body_fits_an_issue_and_keeps_its_end(self):
        text = "\n".join(f"line {i}" for i in range(20000)) + "\n<!-- report-ids {} -->"
        out = refresh.cut(text, refresh.LIMIT, "<!-- report-ids {} -->")
        self.assertLessEqual(len(out), refresh.LIMIT)
        self.assertIn("(cut: too long for an issue)", out)
        self.assertTrue(out.endswith("<!-- report-ids {} -->"))
        self.assertNotIn("line 19999", out)
        self.assertLessEqual(len(refresh.cut(text)), refresh.ISSUE_MAX)

    def test_a_short_body_is_left_as_it_is(self):
        self.assertEqual(refresh.cut("short"), "short")


class FromSite(unittest.TestCase):
    """Render builds with the measurements of the published website (--from-site-only), and never reads another site."""
    def run_main(self, site):
        import contextlib
        import io
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as d:
            out = pathlib.Path(d) / "metrics.json"
            never = mock.Mock(side_effect=AssertionError("a source was read"))
            with mock.patch.object(refresh, "OUT", out), mock.patch.object(refresh, "site_metrics", return_value=site), \
                 mock.patch.object(refresh, "read", never), mock.patch.object(sys, "argv", ["refresh.py", "--from-site-only"]), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(refresh.main(), 0)
            return json.loads(out.read_text(encoding="utf-8")) if out.exists() else None

    def test_published_measurements_are_written(self):
        self.assertEqual(self.run_main({"x": {"stars": 3}}), {"x": {"stars": 3}})

    def test_without_the_website_nothing_is_read_nor_written(self):
        self.assertIsNone(self.run_main(None))

    def test_the_website_file_is_a_table_of_entries(self):
        from unittest import mock
        import contextlib
        import io
        for body, want in ((b'{"x": {"stars": 3}}', {"x": {"stars": 3}}), (b'[1, 2]', None)):
            with mock.patch.object(refresh, "get", return_value=body), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(refresh.site_metrics(), want)


class Get(unittest.TestCase):
    """get() reads at most refresh.MAX_BYTES: a longer answer is refused by name, never held in memory."""

    class Answer:
        def __init__(self, size):
            self.size, self.asked = size, []

        def read(self, n=-1):
            self.asked.append(n)
            return b"x" * (self.size if n < 0 else min(n, self.size))

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def get(self, size):
        from unittest import mock
        answer = self.Answer(size)
        with mock.patch.object(refresh.urllib.request, "urlopen", return_value=answer):
            return refresh.get("https://example.org/feed"), answer

    def test_within_the_cap(self):
        body, answer = self.get(refresh.MAX_BYTES)
        self.assertEqual(len(body), refresh.MAX_BYTES)
        self.assertNotIn(-1, answer.asked)   # never an unbounded read

    def test_over_the_cap(self):
        with self.assertRaises(refresh.TooLarge):
            self.get(refresh.MAX_BYTES + 1)
        with self.assertRaises(refresh.TooLarge):
            self.get(10 * refresh.MAX_BYTES)   # the stream is read up to the cap, not to its end


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
        previous = ('Monthly data report: 4 Nov 2026. Read by the monthly review.\n<!-- report-ids '
                    + json.dumps({"month": month, "date": "4 Nov 2026", "ids": {"read failures": ["a", "b"], "archived": []}}) + " -->")
        when, kept, base = refresh.guard(previous, {"read failures": ["b", "c"], "archived": ["d"]})
        self.assertEqual(when, "4 Nov 2026")
        self.assertEqual(kept, {"read failures": ["b"]})
        self.assertEqual(refresh.guard("", {"read failures": ["b"]}), (None, {}, {}))
        # written again the same month: compared with last month's report, not with itself
        again = "<!-- report-ids " + json.dumps({"month": T.isoformat()[:7], "date": refresh.date_en(T), "ids": {"read failures": ["b", "c"]}, "base": base}) + " -->"
        self.assertEqual(refresh.guard(again, {"read failures": ["b", "c"]})[:2], ("4 Nov 2026", {"read failures": ["b"]}))

    def test_history_that_cannot_be_read(self):
        self.assertEqual(refresh.month_changes(None, set()), ("The `history` branch could not be read this month.", []))
        self.assertIsNone(refresh.archived_since(None, "x"))

    def test_links_that_block_github_come_from_the_links_issue(self):
        report = "### Errors in data/brands.toml\n\n* [503] <https://a.example/> (at 3:8) | Rejected status code: 503\n"
        text, _ = links_issue.body(report, rechecked={"https://a.example/": ("alive", ["200, 200, 200"], None)}, today=dt.date(2026, 11, 25))
        title, lines = refresh.links_blocking(text)
        self.assertEqual(title, "They block GitHub, alive according to Globalping on 25 Nov 2026 (1)")
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
