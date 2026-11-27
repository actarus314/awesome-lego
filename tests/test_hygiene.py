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
