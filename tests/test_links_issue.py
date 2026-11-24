import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
import links_issue  # noqa: E402

REPORT = """## Errors per input

### Errors in data/brands.toml

* [503] <https://a.example/> (at 3:8) | Rejected status code: 503 Service Unavailable
* [503] <https://a.example/> (at 9:8) | Rejected status code: 503 Service Unavailable
* [ERROR] <https://b.example/> (at 5:8) | Network error

### Timeouts in data/clubs.toml

* [TIMEOUT] <https://c.example/> (at 7:8) | Request timed out
"""


class LinksIssue(unittest.TestCase):
    def test_first_run_lists_everything_once(self):
        body = links_issue.body(REPORT)
        self.assertIn("3 links failed", body)
        self.assertNotIn("twice in a row", body)
        self.assertEqual(body.count("<https://a.example/>"), 1)
        self.assertIn("(data/clubs.toml 7:8)", body)

    def test_second_failure_moves_up(self):
        body = links_issue.body(REPORT, "* <https://b.example/> (data/brands.toml 5:8) | Network error")
        twice, once = body.split("## Failed in this run only")
        self.assertIn("<https://b.example/>", twice)
        self.assertNotIn("<https://b.example/>", once)
        self.assertIn("<https://a.example/>", once)


if __name__ == "__main__":
    unittest.main()
