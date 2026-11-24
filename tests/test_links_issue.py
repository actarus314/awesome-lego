import datetime as dt
import json
import pathlib
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.parse
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
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
ALL = ("https://a.example/", "https://b.example/", "https://c.example/")


def probe(status="finished", code=None, raw="", body=None, location=None, source=None):
    r = {"status": status, "statusCode": code, "rawOutput": raw, "rawBody": body, "headers": {"Location": location} if location else {}}
    if source:
        r["failureSource"] = source
    return {"result": r}


class Lychee(unittest.TestCase):
    def test_first_run_lists_everything_once(self):
        text, needed = links_issue.body(REPORT, today=DAY)
        self.assertIn("3 links failed from the machines of GitHub on 25 November 2026.", text)
        self.assertNotIn("Failed twice in a row", text)
        self.assertEqual(text.count("<https://a.example/>"), 1)
        self.assertIn("(data/clubs.toml 7:8)", text)
        self.assertFalse(needed)   # not opened again and failed once only: no person needed yet

    def test_without_globalping_a_second_failure_moves_up_and_needs_a_person(self):
        text, needed = links_issue.body(REPORT, "* <https://b.example/> (data/brands.toml 5:8) | Network error", today=DAY)
        twice, once = text.split("### Failed in this run only")
        self.assertIn("<https://b.example/>", twice)
        self.assertNotIn("<https://b.example/>", once)
        self.assertIn("<https://a.example/>", once)
        self.assertTrue(needed)

    def test_nothing_failed(self):
        text, needed = links_issue.body("", today=DAY)
        self.assertEqual(text.strip(), "Every link answers (25 November 2026).")
        self.assertFalse(needed)

    def test_one_link(self):
        report = "### Errors in data/brands.toml\n\n* [503] <https://a.example/> (at 3:8) | 503\n"
        text, _ = links_issue.body(report, rechecked={"https://a.example/": ("alive", ["200, 200, 200"], None)}, today=DAY)
        self.assertIn("1 link failed from the machines of GitHub on 25 November 2026; 1 was opened again", text)

    def test_dead_pages_without_failures(self):
        dead = [("https://a.example/", "entry `a`", "closed", "`fermeture définitive`")]
        text, needed = links_issue.body("", dead=dead, today=DAY)
        self.assertTrue(text.startswith("Every link answers from the machines of GitHub (25 November 2026)."))
        self.assertIn("## They answer, but the page is dead", text)
        self.assertTrue(needed)


class Globalping(unittest.TestCase):
    def test_verdicts(self):
        v = links_issue.verdict
        self.assertEqual(v([probe("failed", raw="queryA ENOTFOUND x")] * 3)[:2], ("down", ["name not found"] * 3))
        self.assertEqual(v([probe(code=525)] * 3)[0], "down")
        self.assertEqual(v([probe(code=503), probe(code=200), probe(code=200)])[0], "alive")
        self.assertEqual(v([probe(code=403)] * 3)[0], "alive")   # a bot check, as lychee
        self.assertEqual(v([probe(code=301, location="/new")] * 3)[::2], ("redirect", "/new"))
        self.assertEqual(v([probe(code=301)] * 3)[0], "alive")   # a redirect without an address: the server answers
        self.assertEqual(v([probe("offline")] * 3)[0], "unchecked")
        internal = probe("failed", raw="The probe reported an invalid result.", source="internal")
        self.assertEqual(v([internal] * 3)[0], "unchecked")   # a failure of the probe, not of the site
        self.assertEqual(v([internal, internal, probe("failed", raw="timed out")])[0], "unchecked")   # one reading judges nothing
        self.assertEqual(v([internal, probe("failed", raw="ENOTFOUND"), probe("failed", raw="ENOTFOUND")])[0], "down")
        self.assertEqual(v([probe("failed", raw="Client network socket disconnected before secure TLS connection")] * 3)[0], "tls")
        self.assertEqual(links_issue.reason(probe("failed", raw="connect to tlsfast.example failed")["result"]), "`connect to tlsfast.example failed`")
        casino = "<html><head><title>Goldspin Casino France</title></head><body>Spins</body></html>"
        self.assertEqual(v([probe(code=200, body=casino)])[2][0], "taken over")

    def test_body_sorts_by_verdict(self):
        rechecked = {"https://a.example/": ("alive", ["503, 200, 200"], None),
                     "https://b.example/": ("down", ["name not found, name not found, name not found"], None),
                     "https://c.example/": ("alive", ["200, 200, 200"], ("taken over", "`casino` in `Casino`"))}
        text, needed = links_issue.body(REPORT, "<https://b.example/>", rechecked, today=DAY)
        broken = text.split("## Broken")[1].split("##")[0]
        self.assertIn("<https://b.example/> (data/brands.toml 5:8) | GitHub: `Network error` | Globalping: name not found, "
                      "name not found, name not found | also in the previous run", broken)
        self.assertIn("<https://c.example/> (data/clubs.toml 7:8) | taken over", text.split("page is dead")[1])
        blocked = text.split("<details>")[1]
        self.assertIn("alive according to Globalping on 25 November 2026 (1)", blocked)
        self.assertIn("<https://a.example/>", blocked)
        self.assertNotIn("Not opened again", text)
        self.assertTrue(needed)

    def test_only_links_that_block_github_close_the_issue(self):
        rechecked = {u: ("alive", ["200, 200, 200"], None) for u in ALL}
        text, needed = links_issue.body(REPORT, rechecked=rechecked, today=DAY)
        self.assertFalse(needed)
        self.assertIn("(3)</summary>", text)

    def test_refused_secure_connections_are_folded(self):
        rechecked = {u: ("tls", ["TLS error, TLS error, TLS error"], None) for u in ALL}
        text, needed = links_issue.body(REPORT, rechecked=rechecked, today=DAY)
        self.assertFalse(needed)
        self.assertNotIn("## Broken", text)
        self.assertIn("refused by GitHub and by Globalping; a browser often still opens them (3)</summary>", text)

    def test_long_lists_are_shortened_with_their_end_kept(self):
        report = "### Errors in data/brands.toml\n\n" + "".join(
            f"* [503] <https://site{i}.example/{'x' * 80}> (at {i}:8) | Rejected status code: 503\n" for i in range(1, 1200))
        rechecked = {u: ("alive", ["200, 200, 200"], None) for u in links_issue.failures(report)}
        text, _ = links_issue.body(report, rechecked=rechecked, today=DAY)
        self.assertLessEqual(len(text), links_issue.LIMIT)
        self.assertIn("more\n\n</details>", text)
        self.assertIn("(1199)</summary>", text)

    def test_text_of_third_parties_cannot_mention_or_link(self):
        page = "<title>Casino bonus @octocat https://spam.example/x [click](https://evil.example) #1</title>"
        kind, ev = links_issue.classify(page)
        self.assertEqual(kind, "taken over")
        quoted = ev.split(" in ", 1)[1]
        self.assertTrue(quoted.startswith("`") and quoted.endswith("`") and quoted.count("`") == 2)
        report = "### Errors in data/brands.toml\n\n* [503] <https://a.example/> (at 3:8) | Rejected `x` @octocat\n"
        text, _ = links_issue.body(report, rechecked={"https://a.example/": ("down", ["503, 503, 503"], None)}, today=DAY)
        self.assertIn("GitHub: `Rejected 'x' @octocat`", text)

    def api(self, answers, limit=100):
        """A fake Globalping: answers[address] are the results of a measurement of that address."""
        def api(path, body=None, token=None):
            if path == "/limits":
                return {"rateLimit": {"measurements": {"create": {"remaining": limit}}}}
            if path == "/measurements":
                req = body["measurementOptions"]["request"]
                url = urllib.parse.urlunsplit(("https", body["target"], req["path"], req.get("query", ""), ""))
                if url not in answers:
                    raise urllib.error.HTTPError("", 422, "no suitable probes", {}, None)
                return {"id": url}
            return {"status": "finished", "results": answers[path.removeprefix("/measurements/")]}
        return api

    def test_recheck_keeps_to_the_hourly_limit(self):
        api = self.api({u: [probe(code=200)] * 3 for u in ALL}, limit=7)
        out = links_issue.recheck(list(ALL), api=api, sleep=lambda s: None)
        self.assertEqual(sorted(out), ["https://a.example/", "https://b.example/"])   # 7 tests left: 2 links of 3 tests

    def test_recheck_falls_back_to_any_eyeball_probe_and_never_to_data_centres(self):
        made = []

        def api(path, body=None, token=None):
            if path == "/limits":
                return {"rateLimit": {"measurements": {"create": {"remaining": 100}}}}
            if path == "/measurements":
                made.append(body["locations"])
                raise urllib.error.HTTPError("", 422, "no suitable probes", {}, None)
            raise AssertionError(path)
        self.assertEqual(links_issue.recheck(["https://a.example/x?y=1"], api=api, sleep=lambda s: None), {})
        self.assertEqual(made, [links_issue.PROBES, links_issue.FALLBACK])
        self.assertTrue(all("eyeball" in loc["magic"] for locs in made for loc in locs))
        self.assertEqual(links_issue._request("https://a.example/x?y=1")["measurementOptions"]["request"],
                         {"method": "GET", "path": "/x", "query": "y=1"})

    def test_redirects_are_followed_to_where_they_lead(self):
        answers = {"https://a.example/": [probe(code=301, location="https://a.example/new")] * 3,
                   "https://a.example/new": [probe(code=302, location="/gone")] * 3,
                   "https://a.example/gone": [probe(code=404)] * 3,
                   "https://b.example/": [probe(code=301, location="https://b.example/home")] * 3,
                   "https://b.example/home": [probe(code=200)] * 3}
        out = links_issue.recheck(["https://a.example/", "https://b.example/"], api=self.api(answers), sleep=lambda s: None)
        self.assertEqual(out["https://a.example/"][0], "down")
        self.assertEqual(out["https://a.example/"][1][:3], ["301, 301, 301 to https://a.example/new",
                                                            "302, 302, 302 to https://a.example/gone", "404, 404, 404"])
        self.assertTrue(out["https://a.example/"][1][3].startswith("again 90 s later: 301, 301, 301 to"))
        self.assertEqual(out["https://b.example/"][0], "alive")

    def test_a_site_down_for_a_minute_is_not_broken(self):
        reads, pauses = {}, []

        def api(path, body=None, token=None):
            if path == "/limits":
                return {"rateLimit": {"measurements": {"create": {"remaining": 100}}}}
            if path == "/measurements":
                return {"id": body["target"]}
            reads[path] = reads.get(path, 0) + 1
            down = path.endswith("a.example") and reads[path] == 1 or path.endswith("b.example")
            return {"status": "finished", "results": [probe("failed", raw="timed out")] * 3 if down else [probe(code=200)] * 3}
        out = links_issue.recheck(["https://a.example/", "https://b.example/"], api=api, sleep=pauses.append)
        self.assertEqual(out["https://a.example/"][0], "alive")
        self.assertEqual(out["https://b.example/"][:2], ("down", ["timed out, timed out, timed out", "again 90 s later: timed out, timed out, timed out"]))
        self.assertIn(links_issue.CONFIRM_PAUSE, pauses)

    def test_recheck_without_the_service(self):
        def api(path, body=None, token=None):
            raise OSError("down")
        self.assertEqual(links_issue.recheck(["https://a.example/"], api=api), {})

    def test_failures_of_the_previous_run_are_opened_again_first(self):
        urls = [f"https://s{i}.example/" for i in range(30)]
        ordered = links_issue.order_for_recheck(urls, "* <https://s29.example/> previous", today=DAY)
        self.assertEqual(ordered[0], "https://s29.example/")
        self.assertEqual(sorted(ordered), sorted(urls))
        other_week = links_issue.order_for_recheck(urls, "", today=DAY + dt.timedelta(days=7))
        self.assertNotEqual(ordered[1:6], [u for u in other_week if u != "https://s29.example/"][:5])


class DeadPages(unittest.TestCase):
    def page(self, title="", h1="", text="", extra=""):
        return f"<html><head><title>{title}</title>{extra}</head><body><h1>{h1}</h1><p>{text}</p></body></html>"

    def test_dead(self):
        c = links_issue.classify
        self.assertEqual(c(self.page("example.com", text="This domain is for sale!"))[0], "parked or expired")
        self.assertEqual(c('<script>window.onload=function(){window.location.href="/lander"}</script>')[0], "parked or expired")
        self.assertEqual(c(self.page("x", extra='<script src="https://www.hugedomains.com/js/x.js"></script>'))[0], "parked or expired")
        self.assertEqual(c(self.page("Squarespace - Website Expired"))[0], "parked or expired")
        self.assertEqual(c(self.page("Goldspin Casino France"))[0], "taken over")
        self.assertEqual(c(self.page("Shop", extra='<meta name="description" content="Online betting and slot gacor">'))[0], "taken over")
        self.assertEqual(c(self.page("Shop", extra='<meta content="Online betting, it\'s fun" name="description">'))[0], "taken over")
        self.assertEqual(c(self.page("Bricks shop", h1="Unser Shop ist dauerhaft geschlossen"))[0], "closed")
        self.assertEqual(c(self.page("Boutique", text="La boutique a fermé ses portes. Merci à tous."))[0], "closed")
        self.assertEqual(c(self.page("Club", extra="<svg viewBox='0 0 1 1'/>", text="We have closed for good."))[0], "closed")

    def test_traps_stay_healthy(self):
        c = links_issue.classify
        for page in (self.page("Votre spécialiste LEGO et COBI"),
                     self.page("Self-Locking Building Bricks", h1="Slots and studs"),
                     self.page("Brickyes", h1="Slot"),
                     self.page("Museum", text="Open Tuesday to Sunday, closed on Mondays."),
                     self.page("BRICK HAUS", text="Menü öffnen Menü schließen"),
                     self.page("Judi's LEGO blog"),
                     self.page("LEGO Roulette wheel Technic MOC"),
                     self.page("Bellagio casino modular MOC"),
                     self.page("Ford Escort MK2 brick model"),
                     self.page("Forum", extra='<script>var m="Your account has been suspended"</script>', text="My account suspended again"),
                     self.page("Club", text='<a href="https://twitter.com/lander">us</a>'),
                     self.page("Club", extra="<!-- domain parked -->")):
            self.assertIsNone(c(page), page)

    def test_broken_markup_is_read_in_linear_time(self):
        start = time.monotonic()
        links_issue.classify("<html><body>" + "<svg><path/>" * 20000 + "<script>" * 20000)
        self.assertLess(time.monotonic() - start, 3)

    def test_dead_pages_skip_failures(self):
        pages = {"https://a.example/": self.page("Casino"), "https://b.example/": self.page("Bricks")}

        def fetch(url):
            if url == "https://c.example/":
                raise OSError("timeout")
            return pages[url]

        out = links_issue.dead_pages([("a", "https://a.example/"), ("b", "https://b.example/"), ("c", "https://c.example/")], fetch)
        self.assertEqual(out, [("https://a.example/", "entry `a`", "taken over", "`Casino` in `Casino`")])

    def test_entries_leave_platforms_and_closed_entries_out(self):
        with tempfile.TemporaryDirectory() as d:
            (pathlib.Path(d) / "data").mkdir()
            (pathlib.Path(d) / "data" / "x.toml").write_text("\n".join(
                f'[[resource]]\nid = "{i}"\nurl = "{u}"\n' + (f'status = "{s}"\n' if s else "") for i, u, s in (
                    ("site", "https://site.example/", None), ("yt", "https://www.youtube.com/@x", None),
                    ("sub", "https://old.reddit.com/r/lego/", None), ("gone", "https://gone.example/", "dead"),
                    ("old", "https://old.example/", "archived"), ("slow", "https://slow.example/", "slow"))), encoding="utf-8")
            self.assertEqual(links_issue.entries(pathlib.Path(d)), [("site", "https://site.example/"), ("slow", "https://slow.example/")])
        self.assertTrue(links_issue.entries())


class Command(unittest.TestCase):
    def test_main_writes_the_state_and_the_body(self):
        with tempfile.TemporaryDirectory() as d:
            report, previous, state = (pathlib.Path(d) / n for n in ("report.md", "previous.md", "needed.txt"))
            report.write_text(REPORT, encoding="utf-8")
            previous.write_text("", encoding="utf-8")
            with mock.patch.object(links_issue, "recheck", return_value={u: ("down", ["timed out, timed out, timed out"], None) for u in ALL}) as r, \
                 mock.patch.object(links_issue, "dead_pages", return_value=[]), mock.patch("sys.stdout") as out:
                links_issue.main([str(report), str(previous), "--recheck", "--pages", "--state", str(state)])
            self.assertEqual(state.read_text(encoding="utf-8"), "open")
            self.assertEqual(sorted(r.call_args[0][0]), sorted(ALL))
            self.assertIn("## Broken", "".join(c.args[0] for c in out.write.call_args_list))

    def test_the_sample_is_well_formed(self):
        cases = json.loads((ROOT / "tests" / "links-sample.json").read_text(encoding="utf-8"))["cases"]
        verdicts = {"globalping": {"down", "alive", "tls"}, "page": {"healthy", "parked or expired", "taken over", "closed"}}
        for c in cases:
            expected = c["expected"] if isinstance(c["expected"], list) else [c["expected"]]
            self.assertTrue(set(expected) <= verdicts[c["check"]], c)
            self.assertTrue(c["url"].startswith(("https://", "http://")) and c["read"] and c["why"], c)
        single = lambda check: {c["expected"] for c in cases if c["check"] == check and isinstance(c["expected"], str)}
        self.assertEqual(single("globalping"), {"down", "alive"})   # cases with and without the defect
        self.assertEqual(single("page"), verdicts["page"])


if __name__ == "__main__":
    unittest.main()
