#!/usr/bin/env python3
"""Mechanical guards run by Check (skill `audit-depot` of the maintainer, batch "gardes-fous", 26 Nov 2026).

What an audit used to find by hand and a script can see fails here, with a message that says what to fix:
- Python: ruff (unused names and imports, syntax errors) and vulture (functions, classes, variables and attributes
  of the scripts that nothing uses; unused arguments and unreachable code of the tests);
- strings of site-src/strings.json that no page, script or template reads;
- fields of the data block of the page that app.js never reads;
- workflows: every job has `timeout-minutes`; every workflow started by pull requests has a `concurrency` group;
- weight budgets of the files served (tests/budgets.json), checked when site/ is built.

Usage: python3 scripts/hygiene.py [--skip-tools]   (--skip-tools: without ruff and vulture, for the unit tests)
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE_SRC = ROOT / "site-src"
PAGE_CODE = ["app.js", "header.js", "index.html", "header.html", "footer.html", "about.html", "vault.html"]
BUDGETS = ROOT / "tests" / "budgets.json"


def tools(root=ROOT):
    """ruff and vulture on the Python code; their output names file and line. vulture reads the scripts from 60 %
    confidence (functions, classes, variables and attributes that nothing uses), tests/vulture-allow.py naming what the
    standard library calls; scripts, tests and the fuzz targets together from 80 % (unused imports, arguments and
    variables, unreachable code), since unittest finds its test classes and methods by name and a fake keeps the
    parameters of what it replaces."""
    out = []
    allow = [str(root / "tests" / "vulture-allow.py")] if (root / "tests" / "vulture-allow.py").exists() else []
    code = ["scripts", "tests", *(["fuzz"] if (root / "fuzz").is_dir() else [])]   # fuzz/: the fuzz targets, read as the tests
    for cmd in (["ruff", "check", "--select", "F,E9", "--output-format", "concise", "--quiet", *code],
                ["vulture", "scripts", *allow, "--min-confidence", "60"],
                ["vulture", *code, "--exclude", "vulture-allow.py", "--min-confidence", "80"]):
        try:
            r = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
        except FileNotFoundError:
            out.append(f"{cmd[0]} is not installed (pip install --require-hashes --only-binary=:all: -r tests/requirements-check.txt)")
            continue
        if r.returncode:
            out += [f"{cmd[0]}: {line}" for line in (r.stdout + r.stderr).strip().splitlines() if line.strip()]
    return out


def unread_strings(strings=None, code=None):
    """Keys of strings.json read by no page, script or template. A key read by composition ('st_' + status,
    `u_${unit}`) counts as read through its prefix; a key read by tn('k', n) also reads its singular 'k1'.
    Limit: a prefix read by composition covers every key that starts with it, the unread ones included."""
    strings = strings if strings is not None else json.loads((SITE_SRC / "strings.json").read_text(encoding="utf-8"))
    code = code if code is not None else "".join((SITE_SRC / f).read_text(encoding="utf-8") for f in PAGE_CODE) \
        + (ROOT / "scripts" / "build.py").read_text(encoding="utf-8")
    prefixes = set(re.findall(r"""['"`]([a-z][a-z_-]*_)['"`]\s*\+""", code)) | set(re.findall(r"`([a-z][a-z_-]*_)\$\{", code))
    plural = set(re.findall(r"""\btn\(\s*['"]([\w-]+)['"]""", code))
    covers = set(re.findall(r"""['"]([a-z][\w-]*)['"]""", " ".join(re.findall(r"const covers=\[([^\]]*)\]", code))))
    def read(k):
        return (re.search(r"""['"`]%s['"`]""" % re.escape(k), code) or any(k.startswith(p) for p in prefixes)
                or (k.endswith("1") and k[:-1] in plural) or k in covers)
    return [k for k in strings if not read(k)]


def unread_fields(blob_keys=None, code=None):
    """Fields of an entry in the data block of the page that app.js never reads (r.x, r[L].x, r['x']).
    Limit: a field counts as read when its last part (`summary` of `en.summary`) is read anywhere in app.js or header.js."""
    if blob_keys is None:
        sys.path.insert(0, str(ROOT / "scripts"))
        import build  # noqa: E402 (the build is imported only when the check runs on the repository)
        import contextlib, io  # noqa: E401,E402
        with contextlib.redirect_stdout(io.StringIO()):
            cats, _ = build.load()
            data = build.site_data(cats, {})
        data["version"] = "0"
        page = build.page("en", data)
        blob = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>', page, re.S).group(1).replace("\\u003c", "<"))
        blob_keys = set()
        for r in blob["resources"]:
            blob_keys |= {k for k in r if k != "en"} | {"en." + k for k in r.get("en", {})}
    code = code if code is not None else (SITE_SRC / "app.js").read_text(encoding="utf-8") + (SITE_SRC / "header.js").read_text(encoding="utf-8")
    def read(k):
        name = k.split(".")[-1]
        return re.search(r"""\.%s\b|\[['"]%s['"]\]|\b%s:""" % ((re.escape(name),) * 3), code)
    return sorted(k for k in blob_keys if not read(k))


def workflows(folder=None):
    """Jobs without timeout-minutes; workflows run on pull requests without a concurrency group.
    Read as text, in the layout of this repository (two spaces per level); a job that calls a reusable workflow
    (`uses:` at job level) takes its timeouts from that workflow."""
    out = []
    job = re.compile(r"""(?m)^  (["']?)([\w-]+)\1:[ \t]*(?:#.*)?$""")
    for f in sorted((folder or ROOT / ".github" / "workflows").glob("*.yml")):
        text = f.read_text(encoding="utf-8")
        head, _, jobs = text.partition("\njobs:\n")
        marks = list(job.finditer(jobs))
        for i, m in enumerate(marks):
            block = jobs[m.end():marks[i + 1].start() if i + 1 < len(marks) else len(jobs)]
            if re.search(r"(?m)^    uses:", block):
                continue
            if not re.search(r"(?m)^    timeout-minutes:", block):
                out.append(f"{f.name}: job `{m.group(2)}` has no timeout-minutes (a stuck job holds a runner for 6 hours)")
        on = re.search(r"""(?ms)^["']?on["']?:(.*?)(?=^\S|\Z)""", head)
        if on and re.search(r"\bpull_request(_target)?\b", on.group(1)) and not re.search(r"(?m)^concurrency:", head) \
                and not re.search(r"(?m)^    concurrency:", jobs):
            out.append(f"{f.name}: runs on pull requests without a concurrency group (a new push leaves the old run going)")
    return out


def budgets(site=None):
    """Weight of the files served against tests/budgets.json; only when site/ is built."""
    site = site or ROOT / "site"
    if not (site / "index.html").exists():
        return []
    spec = json.loads(BUDGETS.read_text(encoding="utf-8"))
    out = []
    n = len(json.loads((site / "data.json").read_text(encoding="utf-8"))["resources"])
    for path, per in spec["per_resource"].items():  # pages that carry every entry: a budget per entry, so that the directory may grow
        p = site / path
        if p.exists() and p.stat().st_size > per * n:
            out.append(f"site/{path}: {p.stat().st_size / n:.0f} bytes per resource for a budget of {per} (tests/budgets.json, measured {spec['measured']}): "
                       "make it lighter, or raise the budget with a reason in the pull request")
        elif not p.exists():
            out.append(f"budget for {path}, which the build no longer writes: remove it from tests/budgets.json")
    for path, limit in spec["files"].items():
        p = site / path
        if not p.exists():
            out.append(f"budget for {path}, which the build no longer writes: remove it from tests/budgets.json")
        elif p.stat().st_size > limit:
            out.append(f"site/{path}: {p.stat().st_size} bytes for a budget of {limit} (tests/budgets.json, measured {spec['measured']}): "
                       "make it lighter, or raise the budget with a reason in the pull request")
    return out


def main():
    problems = [] if "--skip-tools" in sys.argv else tools()
    problems += [f"site-src/strings.json: `{k}` is read by no page, script or template: remove it, or read it" for k in unread_strings()]
    problems += [f"data block of the page: `{k}` is sent but app.js never reads it: leave it out in build.py (PAGE_UNREAD), or read it"
                 for k in unread_fields()]
    problems += workflows()
    problems += budgets()
    for p in problems:
        print(f"✗ {p}")
    if problems:
        sys.exit(1)
    weights = "weight budgets" if (ROOT / "site" / "index.html").exists() else "no weight budget (site/ not built: python3 scripts/build.py --site-only)"
    print(f"✓ hygiene: {'' if '--skip-tools' in sys.argv else 'Python, '}strings, page data, workflows, {weights}")


if __name__ == "__main__":
    main()
