#!/usr/bin/env python3
"""Notes of the GitHub releases, taken from CHANGELOG.md (workflow Release).

    python3 scripts/release_notes.py section vX.Y            the section of vX.Y, on the standard output (exit 1 if none)
    python3 scripts/release_notes.py stale releases.json DIR  the releases whose notes differ from their section:
                                                             one tag per line, its notes written to DIR/<tag>.md

releases.json is the list GitHub's API returns (`gh api repos/OWNER/REPO/releases --paginate`). A release without
a section of its own (a version never written in CHANGELOG.md) keeps its notes.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def section(text, version):
    """Lines under `## vX.Y ` up to the next version or series heading, as the release shows them."""
    out, inside = [], False
    for line in text.splitlines():
        if line.startswith(f"## {version} "):
            inside = True
            continue
        if line.startswith("## v") or line.startswith("# "):
            inside = False
        if inside:
            out.append(line)
    return "\n".join(out).strip()


def stale(releases, text):
    """(tag, notes) of each release whose notes differ from its section of the changelog."""
    out = []
    for r in releases:
        notes = section(text, r["tag_name"])
        if notes and notes != (r.get("body") or "").strip():
            out.append((r["tag_name"], notes))
    return out


def main(argv):
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    if len(argv) == 2 and argv[0] == "section":
        notes = section(text, argv[1])
        if not notes:
            print(f"No CHANGELOG section for {argv[1]}", file=sys.stderr)
            return 1
        print(notes)
        return 0
    if len(argv) == 3 and argv[0] == "stale":
        releases = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
        if releases and isinstance(releases[0], list):  # gh api --paginate --slurp: one list per page
            releases = [r for page in releases for r in page]
        folder = Path(argv[2])
        folder.mkdir(parents=True, exist_ok=True)
        for tag, notes in stale(releases, text):
            (folder / f"{tag}.md").write_text(notes + "\n", encoding="utf-8")
            print(tag)
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
