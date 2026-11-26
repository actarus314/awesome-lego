#!/usr/bin/env python3
"""Weekly mechanical fixes (workflow Tidy; skill `audit-depot` of the maintainer): what can be corrected without judgement.

- Python: ruff's safe fix of unused imports (F401) in scripts/ and tests/;
- PNG files of media/: lossless compression by oxipng (text chunks kept: the version shown by the README image stays readable).

Writes a summary in Markdown on the standard output; the workflow opens a pull request only when a file changed.
Usage: python3 scripts/tidy.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    lines = []
    try:
        r = subprocess.run(["ruff", "check", "--select", "F401", "--fix", "--quiet", "scripts", "tests"], cwd=ROOT, capture_output=True, text=True)
    except FileNotFoundError:
        sys.exit("ruff is not installed: pip install --require-hashes --only-binary=:all: -r tests/requirements-tidy.txt")
    if r.stdout.strip() or r.stderr.strip():
        lines.append("Python: " + (r.stdout + r.stderr).strip().replace("\n", "; ")[:2000])
    try:
        import oxipng
    except ImportError:
        sys.exit("pyoxipng is not installed: pip install --require-hashes --only-binary=:all: -r tests/requirements-tidy.txt")
    saved = []
    for p in sorted((ROOT / "media").rglob("*.png")):
        if p.name.startswith("site-preview"):
            continue  # the README images change with each version, in the pull request that carries it (rule of CLAUDE.md)
        before = p.stat().st_size
        oxipng.optimize(str(p), level=4)  # lossless; ancillary text chunks are kept (no stripping)
        after = p.stat().st_size
        if after < before:
            saved.append((p.relative_to(ROOT).as_posix(), before, after))
    if saved:
        total = sum(b - a for _, b, a in saved)
        lines.append(f"PNG: {len(saved)} files, {total} bytes saved, lossless:")
        lines += [f"- `{f}`: {b} → {a} bytes" for f, b, a in saved]
    print("\n".join(lines) if lines else "Nothing to tidy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
