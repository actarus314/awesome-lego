#!/usr/bin/env python3
"""Mechanical guards run by Check (skill `audit-depot` of the maintainer, batch "gardes-fous", 26 Nov 2026).

What an audit used to find by hand and a script can see fails here, with a message that says what to fix:
- Python: ruff (unused names and imports, syntax errors) and vulture (dead code, 80 % confidence or more);
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


def tools():
    """ruff and vulture on the Python code; their output names file and line."""
    out = []
    for cmd in (["ruff", "check", "--select", "F,E9", "--output-format", "concise", "--quiet", "scripts", "tests"],
                ["vulture", "scripts", "tests", "--min-confidence", "80"]):
        try:
            r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        except FileNotFoundError:
            out.append(f"{cmd[0]} is not installed (pip install --require-hashes -r tests/requirements-check.txt)")
            continue
        if r.returncode:
            out += [f"{cmd[0]}: {line}" for line in (r.stdout + r.stderr).strip().splitlines() if line.strip()]
    return out


def unread_strings(strings=None, code=None):
    """Keys of strings.json read by no page, script or template. A key read by composition ('st_' + status,
    `u_${unit}`) counts as read through its prefix; a key read by tn('k', n) also reads its singular 'k1'."""
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
    """Fields of an entry in the data block of the page that app.js never reads (r.x, r[L].x, r['x'])."""
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
    """Jobs without timeout-minutes; workflows run on pull requests without a concurrency group."""
    out = []
    for f in sorted((folder or ROOT / ".github" / "workflows").glob("*.yml")):
        text = f.read_text(encoding="utf-8")
        jobs = text.split("\njobs:\n", 1)[1] if "\njobs:\n" in text else ""
        names = re.findall(r"(?m)^  ([\w-]+):\s*$", jobs)
        blocks = re.split(r"(?m)^  [\w-]+:\s*$", jobs)[1:]
        for name, block in zip(names, blocks):
            if "uses: ./" in block or re.search(r"(?m)^    uses:", block):
                continue  # a call of a reusable workflow takes its timeouts from that workflow
            if not re.search(r"(?m)^    timeout-minutes:", block):
                out.append(f"{f.name}: job `{name}` has no timeout-minutes (a stuck job holds a runner for 6 hours)")
        head = text.split("\njobs:\n", 1)[0]
        if re.search(r"(?m)^  pull_request(_target)?:", head) and not re.search(r"(?m)^concurrency:", head) and not re.search(r"(?m)^    concurrency:", jobs):
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
    print("✓ hygiene: Python, strings, page data, workflows, weight budgets")


if __name__ == "__main__":
    main()
