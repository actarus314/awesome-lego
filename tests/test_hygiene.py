"""Each mechanical guard of scripts/hygiene.py fails on a defect planted on purpose and passes on the repository."""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import hygiene  # noqa: E402


class Strings(unittest.TestCase):
    def test_a_key_nobody_reads_is_reported(self):
        code = "t('used');t('st_'+s);tn('u_sets',n);const covers=['official'];"
        strings = {"used": 1, "st_active": 1, "u_sets": 1, "u_sets1": 1, "official": 1, "forgotten": 1}
        self.assertEqual(hygiene.unread_strings(strings, code), ["forgotten"])

    def test_the_repository_reads_every_string(self):
        self.assertEqual(hygiene.unread_strings(), [])


class Fields(unittest.TestCase):
    def test_a_field_the_page_never_reads_is_reported(self):
        self.assertEqual(hygiene.unread_fields({"name", "en.summary", "confidence"}, "r.name;r[L].summary"), ["confidence"])

    def test_the_page_reads_every_field_it_receives(self):
        self.assertEqual(hygiene.unread_fields(), [])


class Workflows(unittest.TestCase):
    JOB = "    runs-on: ubuntu-latest\n    timeout-minutes: 5\n    steps: []\n"

    def check(self, **files):
        with tempfile.TemporaryDirectory() as d:
            for name, text in files.items():
                (Path(d) / f"{name}.yml").write_text(text, encoding="utf-8")
            return hygiene.workflows(Path(d))

    def test_a_job_without_timeout_is_reported_however_its_name_is_written(self):
        steps = "    runs-on: ubuntu-latest\n    steps:\n      - uses: ./.github/actions/local\n"
        out = self.check(a="on: push\njobs:\n  plain:\n" + steps + "  commented:   # a note\n" + steps + "  'quoted':\n" + steps
                         + "  called:\n    uses: ./.github/workflows/b.yml\n")
        self.assertEqual(sorted(x.split("`")[1] for x in out), ["commented", "plain", "quoted"])  # the call of a reusable workflow is not

    def test_a_pull_request_workflow_without_concurrency_is_reported_in_each_form_of_on(self):
        out = self.check(block="on:\n  pull_request:\njobs:\n  a:\n" + self.JOB, flow="on: [push, pull_request]\njobs:\n  a:\n" + self.JOB,
                         word="on: pull_request_target\njobs:\n  a:\n" + self.JOB, push="on: push\njobs:\n  a:\n" + self.JOB,
                         grouped="on: pull_request\nconcurrency: x\njobs:\n  a:\n" + self.JOB)
        self.assertEqual(sorted(x.split(":")[0] for x in out), ["block.yml", "flow.yml", "word.yml"])

    def test_the_workflows_of_the_repository(self):
        self.assertEqual(hygiene.workflows(), [])


class Budgets(unittest.TestCase):
    def test_a_page_over_its_budget_per_resource(self):
        with tempfile.TemporaryDirectory() as d:
            site = Path(d)
            (site / "index.html").write_text("x" * 300, encoding="utf-8")
            (site / "data.json").write_text(json.dumps({"resources": [{}, {}]}), encoding="utf-8")
            spec = Path(d) / "budgets.json"
            spec.write_text(json.dumps({"measured": "test", "per_resource": {"index.html": 100}, "files": {}}), encoding="utf-8")
            old, hygiene.BUDGETS = hygiene.BUDGETS, spec
            try:
                self.assertEqual(len(hygiene.budgets(site)), 1)
                spec.write_text(json.dumps({"measured": "test", "per_resource": {"index.html": 200}, "files": {}}), encoding="utf-8")
                self.assertEqual(hygiene.budgets(site), [])
            finally:
                hygiene.BUDGETS = old



class MachineAccess(unittest.TestCase):
    """The étalon of dev/lots/acces-machines.md: a complete site passes; a missing file, an address of llms.txt that leads
    nowhere, a broken footer link and a robots.txt that refuses a robot each give a message."""
    P = hygiene.PAGES

    def site(self, d):
        s = Path(d)
        (s / "fr" / "about").mkdir(parents=True)
        (s / "about").mkdir()
        for f in ("data.json", "sitemap.xml", "fr/index.html", "about/index.html", "fr/about/index.html", "404.html"):
            (s / f).write_text("{}" if f.endswith(".json") else "", encoding="utf-8")
        (s / "index.html").write_text(f'<link rel="describedby" type="text/plain" href="{self.P}llms.txt"><a href="index.md" type="text/markdown">t</a>'
                                      '<a href="data.json" type="application/json">j</a><a href="https://example.org/x" rel="noopener">x</a>', encoding="utf-8")
        (s / "fr" / "about" / "index.html").write_text('<a href="../index.md" type="text/markdown">t</a><a href="../../data.json" type="application/json">j</a>', encoding="utf-8")
        (s / "llms.txt").write_text(f"# A\n\n- [List]({self.P}index.md): all\n- [Liste]({self.P}fr/index.md)\n- [About]({self.P}fr/about/)\n", encoding="utf-8")
        (s / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {self.P}sitemap.xml\n", encoding="utf-8")
        for f in hygiene.MD_PATH.values():
            (s / f).write_text(f"# List\n\n[site]({self.P})\n", encoding="utf-8")
        return s

    def test_a_complete_site_passes(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(hygiene.machine_access(self.site(d)), [])

    def test_each_planted_defect_is_reported(self):  # each with the file and the address it names
        P = self.P
        defects = {
            "index.md missing": (lambda s: (s / "index.md").unlink(), ["site/index.md is not built", f"site/llms.txt: {P}index.md leads to no built file",
                                                                        f"site/index.html: {P}index.md leads to no built file"]),
            "llms.txt missing": (lambda s: (s / "llms.txt").unlink(), ["site/llms.txt is not built", f"site/index.html: {P}llms.txt leads to no built file"]),
            "address of llms.txt": (lambda s: (s / "llms.txt").write_text(f"# A\n\n- [Gone]({P}gone.xml)\n", encoding="utf-8"),
                                    [f"site/llms.txt: {P}gone.xml leads to no built file"]),
            "footer link": (lambda s: (s / "fr" / "about" / "index.html").write_text('<a href="data.json" type="application/json">j</a>', encoding="utf-8"),
                            [f"site/fr/about/index.html: {P}fr/about/data.json leads to no built file"]),
            "robots refusing": (lambda s: (s / "robots.txt").write_text(f"User-agent: GPTBot\nDisallow: /\n\nSitemap: {P}sitemap.xml\n", encoding="utf-8"),
                                ["site/robots.txt: 'Disallow: /' refuses something"]),
            "robots without sitemap": (lambda s: (s / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8"),
                                       [f"site/robots.txt: no line 'Sitemap: {P}sitemap.xml'"]),
        }
        for name, (plant, expected) in defects.items():
            with self.subTest(name), tempfile.TemporaryDirectory() as d:
                s = self.site(d)
                plant(s)
                found = hygiene.machine_access(s)
                self.assertEqual(len(found), len(expected), found)
                for e in expected:
                    self.assertTrue(any(f.startswith(e) for f in found), (e, found))

    def test_one_message_per_page_and_address(self):  # a home page links the list from its head, its noscript line and its footer
        with tempfile.TemporaryDirectory() as d:
            s = self.site(d)
            (s / "index.html").write_text('<a href="gone.md" type="text/markdown">a</a>' * 3, encoding="utf-8")
            self.assertEqual(hygiene.machine_access(s), [f"site/index.html: {self.P}gone.md leads to no built file"])

    def test_nothing_without_a_built_site(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(hygiene.machine_access(Path(d)), [])


if __name__ == "__main__":
    unittest.main()


TOOLS = shutil.which("ruff") and shutil.which("vulture")


@unittest.skipIf(not TOOLS and not os.environ.get("CI"), "ruff and vulture are not installed (tests/requirements-check.txt)")
class Tools(unittest.TestCase):
    def test_unused_code_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "scripts").mkdir()
            (Path(d) / "tests").mkdir()
            shutil.copy(ROOT / "tests" / "vulture-allow.py", Path(d) / "tests")
            (Path(d) / "scripts" / "x.py").write_text(
                "import os\nimport html.parser\nLEFT = 1\n\n\ndef never():\n    return 1\n\n\nclass P(html.parser.HTMLParser):\n"
                "    def handle_data(self, data):\n        print(data)\n\n\ndef main(unused):\n    return 2\n    print('after return')\n\n\nmain(0)\nP()\n",
                encoding="utf-8")
            out = "\n".join(hygiene.tools(Path(d)))
        for found in ("F401", "'never'", "'LEFT'", "'unused'", "unreachable"):
            self.assertIn(found, out)
        self.assertNotIn("handle_data", out)  # called by the standard library: named in tests/vulture-allow.py

    def test_the_repository_has_no_unused_code(self):
        self.assertEqual(hygiene.tools(), [])


class Main(unittest.TestCase):
    def run_main(self, **found):
        names = ("unread_strings", "unread_fields", "workflows", "budgets")
        with contextlib.ExitStack() as stack, contextlib.redirect_stdout(io.StringIO()) as buf:
            for n in names:
                stack.enter_context(mock.patch.object(hygiene, n, return_value=found.get(n, [])))
            stack.enter_context(mock.patch.object(sys, "argv", ["hygiene.py", "--skip-tools"]))
            try:
                hygiene.main()
                code = 0
            except SystemExit as e:
                code = e.code
        return code, buf.getvalue()

    def test_any_finding_fails(self):
        for n in ("unread_strings", "unread_fields", "workflows", "budgets"):
            code, text = self.run_main(**{n: ["planted"]})
            self.assertEqual(code, 1, n)
            self.assertIn("✗", text)

    def test_nothing_found_passes(self):
        self.assertEqual(self.run_main()[0], 0)
