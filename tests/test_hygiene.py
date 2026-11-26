"""Each mechanical guard of scripts/hygiene.py fails on a defect planted on purpose and passes on the repository."""
import json
import sys
import tempfile
import unittest
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
    def test_a_job_without_timeout_and_a_pull_request_workflow_without_concurrency(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "x.yml").write_text("name: X\non:\n  pull_request:\njobs:\n  a:\n    runs-on: ubuntu-latest\n    steps: []\n", encoding="utf-8")
            out = hygiene.workflows(Path(d))
        self.assertEqual(len(out), 2)

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
