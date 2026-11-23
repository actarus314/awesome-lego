#!/usr/bin/env python3
"""Draft a CHANGELOG entry: what changed in data/ since a git reference (default: the latest tag).

Usage: python3 scripts/changelog.py [REF]
Prints resources added, removed and corrected, and changes to the README selection.
Fields refreshed on every check (checked, last_activity, status, confidence) are not counted as corrections.
"""
import pathlib
import subprocess
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parent.parent
QUIET = {"checked", "last_activity", "status", "confidence", "sources"}


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def resources(text_by_file):
    out = {}
    for name, text in text_by_file.items():
        for r in tomllib.loads(text).get("resource", []):
            out[r["id"]] = r
    return out


def main():
    ref = sys.argv[1] if len(sys.argv) > 1 else git("describe", "--tags", "--abbrev=0").strip()
    files = [f for f in git("ls-tree", "--name-only", ref, "data/").split() if f.endswith(".toml")]
    old = resources({f: git("show", f"{ref}:{f}") for f in files})
    new = resources({str(p): p.read_text(encoding="utf-8") for p in (ROOT / "data").glob("*.toml")})
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    corrected = sorted(i for i in set(new) & set(old)
                       if {k: v for k, v in new[i].items() if k not in QUIET | {"featured"}}
                       != {k: v for k, v in old[i].items() if k not in QUIET | {"featured"}})
    selected = sorted(i for i in new if new[i].get("featured") and not old.get(i, {}).get("featured"))
    unselected = sorted(i for i in old if old[i].get("featured") and not new.get(i, {}).get("featured"))
    name = lambda i: (new.get(i) or old.get(i))["name"]
    print(f"Changes since {ref}: {len(added)} added, {len(removed)} removed, {len(corrected)} corrected; "
          f"README selection: {len(selected)} in, {len(unselected)} out.")
    for label, ids in (("Added", added), ("Removed", removed), ("Corrected", corrected),
                       ("Now in the README", selected), ("Out of the README", unselected)):
        if ids:
            print(f"- {label}: " + ", ".join(name(i) for i in ids) + ".")


if __name__ == "__main__":
    main()
