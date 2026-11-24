import datetime as dt
import pathlib
import sys
import unittest
import urllib.error

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
DAY = dt.date(2026, 11, 25)


def probe(status="finished", code=None, raw="", body=None):
    return {"result": {"status": status, "statusCode": code, "rawOutput": raw, "rawBody": body}}


class Lychee(unittest.TestCase):
    def test_first_run_lists_everything_once(self):
        text, needed = links_issue.body(REPORT, today=DAY)
        self.assertIn("3 links failed from the machines of GitHub on 25 November 2026.", text)
        self.assertNotIn("Failed twice in a row", text)
        self.assertEqual(text.count("<https://a.example/>"), 1)
        self.assertIn("(data/clubs.toml 7:8)", text)
        self.assertTrue(needed)

    def test_without_globalping_a_second_failure_moves_up(self):
        text, _ = links_issue.body(REPORT, "* <https://b.example/> (data/brands.toml 5:8) | Network error", today=DAY)
        twice, once = text.split("### Failed in this run only")
        self.assertIn("<https://b.example/>", twice)
        self.assertNotIn("<https://b.example/>", once)
        self.assertIn("<https://a.example/>", once)

    def test_nothing_failed(self):
        text, needed = links_issue.body("", today=DAY)
        self.assertEqual(text.strip(), "Every link answers (25 November 2026).")
        self.assertFalse(needed)


class Globalping(unittest.TestCase):
    def test_verdicts(self):
        v = links_issue.verdict
        self.assertEqual(v([probe("failed", raw="queryA ENOTFOUND x")] * 3)[:2], ("down", ["name not found"] * 3))
        self.assertEqual(v([probe(code=525)] * 3)[0], "down")
        self.assertEqual(v([probe(code=503), probe(code=200), probe(code=200)])[0], "alive")
        self.assertEqual(v([probe(code=301)] * 3)[0], "alive")   # a redirect: left to Data fixes
        self.assertEqual(v([probe(code=403)] * 3)[0], "alive")   # a bot check, as lychee
        self.assertEqual(v([probe("offline")] * 3)[0], "unchecked")
        casino = "<html><head><title>Goldspin Casino France</title></head><body>Spins</body></html>"
        self.assertEqual(v([probe(code=200, body=casino)])[2][0], "taken over")

    def test_body_sorts_by_verdict(self):
        rechecked = {"https://a.example/": ("alive", ["503", "200", "200"], None),
                     "https://b.example/": ("down", ["name not found"] * 3, None),
                     "https://c.example/": ("alive", ["200"] * 3, ("taken over", "casino: “Casino”"))}
        text, needed = links_issue.body(REPORT, "<https://b.example/>", rechecked, today=DAY)
        broken = text.split("## Broken")[1].split("##")[0]
        self.assertIn("<https://b.example/> (data/brands.toml 5:8) | GitHub: Network error | Globalping: name not found, "
                      "name not found, name not found | also last week", broken)
        self.assertIn("<https://c.example/> (data/clubs.toml 7:8) | taken over", text.split("page is dead")[1])
        blocked = text.split("<details>")[1]
        self.assertIn("alive according to Globalping on 25 November 2026 (1)", blocked)
        self.assertIn("<https://a.example/>", blocked)
        self.assertNotIn("Not opened again", text)
        self.assertTrue(needed)

    def test_only_links_that_block_github_close_the_issue(self):
        rechecked = {u: ("alive", ["200"] * 3, None) for u in ("https://a.example/", "https://b.example/", "https://c.example/")}
        text, needed = links_issue.body(REPORT, rechecked=rechecked, today=DAY)
        self.assertFalse(needed)
        self.assertIn("(3)</summary>", text)

    def test_recheck_keeps_to_the_hourly_limit_and_falls_back_to_any_probe(self):
        calls = []

        def api(path, body=None, token=None):
            calls.append((path, body))
            if path == "/limits":
                return {"rateLimit": {"measurements": {"create": {"remaining": 7}}}}
            if path == "/measurements":
                if body["locations"] == links_issue.PROBES and body["target"] == "a.example":
                    raise urllib.error.HTTPError("", 422, "no suitable probes", {}, None)
                return {"id": body["target"]}
            return {"status": "finished", "results": [probe(code=200)] * 3}

        out = links_issue.recheck(["https://a.example/x?y=1", "https://b.example/", "https://c.example/"], api=api, sleep=lambda s: None)
        self.assertEqual(sorted(out), ["https://a.example/x?y=1", "https://b.example/"])   # 7 tests left: 2 links of 3 tests
        made = [b for p, b in calls if p == "/measurements"]
        self.assertEqual([b["locations"] for b in made][:2], [links_issue.PROBES, links_issue.FALLBACK])
        self.assertEqual(made[0]["measurementOptions"]["request"], {"method": "GET", "path": "/x", "query": "y=1"})

    def test_recheck_without_the_service(self):
        def api(path, body=None, token=None):
            raise OSError("down")
        self.assertEqual(links_issue.recheck(["https://a.example/"], api=api), {})


class DeadPages(unittest.TestCase):
    def page(self, title="", h1="", text="", extra=""):
        return f"<html><head><title>{title}</title>{extra}</head><body><h1>{h1}</h1><p>{text}</p></body></html>"

    def test_dead(self):
        c = links_issue.classify
        self.assertEqual(c(self.page("example.com", text="This domain is for sale!"))[0], "parked or expired")
        self.assertEqual(c('<script>window.onload=function(){window.location.href="/lander"}</script>')[0], "parked or expired")
        self.assertEqual(c(self.page("Squarespace - Website Expired"))[0], "parked or expired")
        self.assertEqual(c(self.page("Goldspin Casino France"))[0], "taken over")
        self.assertEqual(c(self.page("Shop", extra='<meta name="description" content="Online betting and slot gacor">'))[0], "taken over")
        self.assertEqual(c(self.page("Bricks shop", h1="Unser Shop ist dauerhaft geschlossen"))[0], "closed")
        self.assertEqual(c(self.page("Boutique", text="La boutique a fermé ses portes. Merci à tous."))[0], "closed")

    def test_traps_stay_healthy(self):
        c = links_issue.classify
        for page in (self.page("Votre spécialiste LEGO et COBI"),
                     self.page("Self-Locking Building Bricks", h1="Slots and studs"),
                     self.page("Brickyes", h1="Slot"),
                     self.page("Museum", text="Open Tuesday to Sunday, closed on Mondays."),
                     self.page("BRICK HAUS", text="Menü öffnen Menü schließen"),
                     self.page("Brick club", text="Bricks, trains and a roulette of colours")):
            self.assertIsNone(c(page), page)

    def test_dead_pages_skip_failures(self):
        pages = {"https://a.example/": self.page("Casino"), "https://b.example/": self.page("Bricks")}

        def fetch(url):
            if url == "https://c.example/":
                raise OSError("timeout")
            return pages[url]

        out = links_issue.dead_pages([("a", "https://a.example/"), ("b", "https://b.example/"), ("c", "https://c.example/")], fetch)
        self.assertEqual(out, [("https://a.example/", "entry `a`", "taken over", "Casino: “Casino”")])

    def test_entries_leave_platforms_out(self):
        urls = [u for _, u in links_issue.entries()]
        self.assertTrue(urls)
        self.assertFalse([u for u in urls if "youtube.com" in u or "reddit.com" in u or "github.com/" in u])


if __name__ == "__main__":
    unittest.main()
