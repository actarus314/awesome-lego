"""The check of .github/workflows/fixes.yml, job "open": the patch handed over by the job that reads third-party sites
is applied only if it is a plain edit of data/<name>.toml, README.md or full-list.md. The script is read from the
workflow itself and run in a scratch repository against a sound patch and hostile ones. Needs bash, git and iconv."""
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
STEP = "Check the patch, then apply it"


def step_script():
    """The `run: |` block of the step named STEP, as written in fixes.yml."""
    lines = (ROOT / ".github" / "workflows" / "fixes.yml").read_text(encoding="utf-8").splitlines()
    i = next(k for k, l in enumerate(lines) if l.strip().startswith("- name: " + STEP))
    j = next(k for k in range(i, len(lines)) if lines[k].strip() == "run: |")
    ind = len(lines[j + 1]) - len(lines[j + 1].lstrip())
    out = []
    for l in lines[j + 1:]:
        if l.strip() and len(l) - len(l.lstrip()) < ind:
            break
        out.append(l[ind:])
    return "\n".join(out) + "\n"


@unittest.skipUnless(shutil.which("git") and shutil.which("bash") and shutil.which("iconv"), "needs git, bash and iconv")
class PatchCheck(unittest.TestCase):
    def setUp(self):
        self.d = pathlib.Path(tempfile.mkdtemp())
        self.repo, self.tmp = self.d / "repo", self.d / "tmp"
        (self.repo / "data").mkdir(parents=True)
        (self.repo / ".github").mkdir()
        (self.tmp / "fixes").mkdir(parents=True)
        (self.repo / "data" / "events.toml").write_text("[[resource]]\nid = \"a\"\nurl = \"https://old.example/\"\n", encoding="utf-8")
        (self.repo / "README.md").write_text("# Awesome\n", encoding="utf-8")
        (self.repo / "full-list.md").write_text("# List\n", encoding="utf-8")
        (self.repo / ".github" / "fixes.yml").write_text("name: x\n", encoding="utf-8")
        self.git("init", "-q")
        self.git("add", "-A")
        self.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base")

    def tearDown(self):
        shutil.rmtree(self.d)

    def git(self, *a):
        return subprocess.run(["git", *a], cwd=self.repo, check=True, capture_output=True).stdout

    def patch(self, change, binary=False):
        """The patch of `change` (a function on the repository), as the job "find" would hand it over; the tree is reset after."""
        change(self.repo)
        self.git("add", "-A")
        p = self.git("diff", "--cached", *(["--binary"] if binary else []))
        self.git("reset", "-q", "--hard")
        self.git("clean", "-qfdx")
        return p

    def run_check(self, patch):
        (self.tmp / "fixes" / "fixes.patch").write_bytes(patch)
        (self.tmp / "fixes" / "fixes.md").write_text("- a: moved\n" * 9000, encoding="utf-8")  # longer than a body
        env = dict(os.environ, FIXES=str(self.tmp / "fixes"), RUNNER_TEMP=str(self.tmp))
        r = subprocess.run(["bash", "-c", step_script()], cwd=self.repo, env=env, capture_output=True, text=True)
        status = self.git("status", "--porcelain", "--untracked-files=all").decode()
        return r.returncode, r.stdout + r.stderr, status

    def test_a_plain_edit_is_applied_and_shown(self):
        p = self.patch(lambda r: (r / "data" / "events.toml").write_text("[[resource]]\nid = \"a\"\nurl = \"https://new.example/\"\n", encoding="utf-8"))
        code, out, status = self.run_check(p)
        self.assertEqual(code, 0, out)
        self.assertEqual(status, " M data/events.toml\n")
        body = (self.tmp / "body.md").read_text(encoding="utf-8")
        self.assertIn("data/events.toml | 2 +-", body)
        self.assertLessEqual(len(body), 60000)

    def hostile(self, change, binary=False):
        code, out, status = self.run_check(self.patch(change, binary))
        self.assertNotEqual(code, 0, out)
        self.assertEqual(status, "", "the tree was changed before the patch was refused")
        self.assertIn("::error::", out)

    def test_a_link_is_refused(self):
        self.hostile(lambda r: os.symlink("../.github/fixes.yml", r / "data" / "evil.toml"))

    def test_a_new_file_is_refused(self):
        self.hostile(lambda r: (r / "data" / "new.py").write_text("x\n"))

    def test_a_deletion_is_refused(self):
        self.hostile(lambda r: (r / "full-list.md").unlink())

    def test_a_change_of_mode_is_refused(self):
        self.hostile(lambda r: os.chmod(r / "README.md", 0o755))

    def test_another_path_is_refused(self):
        self.hostile(lambda r: (r / ".github" / "fixes.yml").write_text("name: y\n"))

    def test_a_binary_patch_is_refused(self):
        self.hostile(lambda r: (r / "README.md").write_bytes(b"\x00\x01binary\x00"), binary=True)

    def test_a_patch_over_one_megabyte_is_refused(self):
        self.hostile(lambda r: (r / "README.md").write_text("x" * 1_100_000 + "\n"))

    def test_the_step_holds_no_token(self):
        y = (ROOT / ".github" / "workflows" / "fixes.yml").read_text(encoding="utf-8")
        block = y[y.index("- name: " + STEP):]
        block = block[:block.index("\n      - ", 1)]
        self.assertNotRegex(block, r"secrets\.|GH_TOKEN|GITHUB_TOKEN|steps\.app|github\.token")


if __name__ == "__main__":
    unittest.main()
