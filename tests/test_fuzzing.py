"""The findings of the fuzz targets (fuzz/, weekly workflow Fuzzing), each replayed on the script it was found in."""
import email.message
import pathlib
import sys
import unittest
import urllib.error
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
import autofix  # noqa: E402
import discover_feeds  # noqa: E402
import links_issue  # noqa: E402
import refresh  # noqa: E402


def redirect(location, code=301):
    headers = email.message.Message()
    headers["Location"] = location
    return urllib.error.HTTPError("https://club.example/news/", code, "Moved", headers, None)


class Answer:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False


class Opener:
    """The answers of the servers, in order: an exception to raise or an answer."""

    def __init__(self, *answers):
        self.answers = list(answers)

    def open(self, _req, **_kwargs):
        a = self.answers.pop(0)
        if isinstance(a, Exception):
            raise a
        return a


class Feed(unittest.TestCase):
    def test_a_date_that_is_no_day_is_left_out(self):   # fuzz/feed_fuzzer.py, 27 Nov 2026
        feed = (b'<?xml version="1.0"?><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" '
                b'xmlns:dc="http://purl.org/dc/elements/1.1/"><item><dc:date>2022-09-81</dc:date></item>'
                b'<item><dc:date>2021-05-04</dc:date></item></rdf:RDF>')
        self.assertEqual(refresh.newest_date(feed), "2021-05-04")

    def test_digits_of_other_scripts_are_no_date(self):
        self.assertIsNone(refresh.newest_date("<a><updated>1٠٢٣-٠٤-٠٥</updated></a>".encode()))

    def test_dates_still_read(self):
        feed = b"<rss><item><pubDate>Sat, 14 Nov 2026 09:30:00 +0100</pubDate></item><item><updated>2026-11-15T08:00Z</updated></item></rss>"
        self.assertEqual(refresh.newest_date(feed), "2026-11-15")


class Discover(unittest.TestCase):
    def test_an_address_urllib_cannot_read_is_skipped(self):   # fuzz/page_fuzzer.py, 27 Nov 2026
        page = (b'<link rel="alternate" type="application/rss+xml" href="http://[x">'
                b'<link rel="alternate" type="application/rss+xml" href="/news/feed.xml">')
        feed = b"<rss><item><pubDate>Sat, 14 Nov 2026 09:30:00 +0100</pubDate></item></rss>"
        get = lambda url: (url, page) if url == "https://club.example/news/" else (url, feed)
        with mock.patch.object(discover_feeds, "get", get):
            self.assertEqual(discover_feeds.find({"url": "https://club.example/news/"}), "https://club.example/news/feed.xml")


class Recheck(unittest.TestCase):
    def test_a_location_urllib_cannot_read_leaves_the_link_alive(self):   # fuzz/globalping_fuzzer.py, 27 Nov 2026
        moved = {"result": {"status": "finished", "statusCode": 301, "rawOutput": "", "rawBody": None, "headers": {"location": "http://[x"}}}

        def api(path, body=None, token=None):
            if path == "/limits":
                return {"rateLimit": {"measurements": {"create": {"remaining": 30}}}}
            if path == "/measurements":
                return {"id": "1"}
            return {"status": "finished", "results": [moved] * 3}
        out = links_issue.recheck(["https://a.example/"], api=api, sleep=lambda _s: None)
        self.assertEqual(out["https://a.example/"], ("alive", ["301, 301, 301"], None))


class Moved(unittest.TestCase):
    def test_an_address_without_a_scheme_is_left_alone(self):   # fuzz/redirect_fuzzer.py, 27 Nov 2026: "URL:" is unwrapped by urllib
        with mock.patch.object(autofix, "OPENER", Opener(redirect("URL:++x"))):
            self.assertIsNone(autofix.moved("https://club.example/news/"))

    def test_control_characters_never_reach_the_data(self):   # fuzz/redirect_fuzzer.py: a fragment is never sent to the server
        for c in ("\x00", "\x01", "\x1f", "\x7f"):
            with mock.patch.object(autofix, "OPENER", Opener(redirect(f"https://club.example/new#a{c}b"), Answer())):
                self.assertIsNone(autofix.moved("https://club.example/news/"), repr(c))

    def test_a_malformed_location_is_left_alone(self):   # relecture de #39: urljoin raises on an unclosed IPv6 bracket
        for loc in ("http://[x", "//[x", "https://[::1"):
            with mock.patch.object(autofix, "OPENER", Opener(redirect(loc))):
                self.assertIsNone(autofix.moved("https://club.example/news/"), loc)

    def test_an_address_without_a_host_is_left_alone(self):   # Fuzzing, first run on GitHub (27 Nov 2026): "http://::"
        for loc in ("http://::", "http://:80/x", "https://@/x"):
            with mock.patch.object(autofix, "OPENER", Opener(redirect(loc), Answer())):
                self.assertIsNone(autofix.moved("https://club.example/news/"), loc)

    def test_a_permanent_move_is_still_followed(self):
        with mock.patch.object(autofix, "OPENER", Opener(redirect("/new#top"), Answer())):
            self.assertEqual(autofix.moved("https://club.example/news/"), "https://club.example/new#top")


if __name__ == "__main__":
    unittest.main()
