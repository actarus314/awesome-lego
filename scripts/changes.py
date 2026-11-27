#!/usr/bin/env python3
"""Fragments of changes/: what each pull request changes, assembled after the merge into the CHANGELOG.md entry of
the next version by the workflow Version (standard library only).

A pull request never writes VERSION, a CHANGELOG.md section, README.md, full-list.md or the README images: it adds
changes/<name>.md (name: lowercase letters, digits and hyphens), for example

    type: minor

    Website: the about page keeps the place being read when the language changes. Feed: named Awesome LEGO.

type: major (a change of structure or data format), minor (content or website) or none (automation, activity data,
the README alone: no number, the fragment waits and the entry of the next version cites it). A major fragment adds
a line `series: <one sentence>` under its type: the heading of the new series of versions. The text says what
changes in two sentences, CHANGELOG_MAX characters at most (scripts/build.py).

Usage:
  python3 scripts/changes.py check [--base REF] [--strict]
      every fragment well formed. --base REF (Check on a pull request: the branch it merges into): the pull request
      leaves VERSION, the sections of CHANGELOG.md, the generated files and the README images to Version, and is
      warned when it changes the data or the website without a fragment. --strict (the pull request of Version):
      no major or minor fragment is left.
  python3 scripts/changes.py assemble [--date YYYY-MM-DD]
      VERSION raised by the strongest type, the entry written at the top of CHANGELOG.md, the fragments removed;
      prints version=X.Y (for $GITHUB_OUTPUT), or nothing and changes nothing when every fragment is of type none.
"""
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import CHANGELOG_MAX, FILES, ID, README_IMAGES  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TYPES = ("major", "minor", "none")  # strongest first
LEFT_TO_VERSION = ["VERSION", *FILES.values(), *(f"media/{n}" for n in README_IMAGES)]
CONTENT = re.compile(r"^(data/[^/]+\.toml|site-src/|media/)")  # what a reader sees: a pull request that changes it says so in a fragment


def parse(path):
    """(type, series, text) of a fragment, or raises ValueError with what to fix."""
    if path.suffix != ".md" or not ID.fullmatch(path.stem):
        raise ValueError("name a fragment <name>.md, with lowercase letters, digits and hyphens")
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    m = re.fullmatch(r"type: (\S+)", lines[0].strip()) if lines else None
    if not m or m.group(1) not in TYPES:
        raise ValueError("the first line is `type: major`, `type: minor` or `type: none`")
    kind, rest, series = m.group(1), lines[1:], ""
    if rest and rest[0].startswith("series:"):
        series, rest = rest[0].removeprefix("series:").strip(), rest[1:]
    if kind == "major" and not series:
        raise ValueError("a major fragment says the heading of its series on a second line, `series: <one sentence>`")
    if kind != "major" and series:
        raise ValueError("only a major fragment opens a series (`series:`)")
    if not rest or rest[0].strip():
        raise ValueError("a blank line separates the type from the text")
    body = [l.strip() for l in rest[1:]]
    if not body or "" in body:
        raise ValueError("the text is one paragraph, under the blank line")
    text = " ".join(body)
    if text.startswith("#"):
        raise ValueError("the text is no heading: Version writes the heading of the version")
    if len(text) > CHANGELOG_MAX:
        raise ValueError(f"{len(text)} characters, {CHANGELOG_MAX} at most: say what changes in two sentences, the details go to the pull request")
    return kind, series, text


def fragments(folder):
    """[(path, type, series, text)] in the order of the entry (strongest type first, then by name), and the errors."""
    out, errors = [], []
    for p in sorted(folder.iterdir()) if folder.is_dir() else []:
        try:
            out.append((p, *parse(p)))
        except ValueError as e:
            errors.append(f"changes/{p.name}: {e}")
    out.sort(key=lambda f: TYPES.index(f[1]))
    return out, errors


def assemble(found, version, changelog, date):
    """(new version, new CHANGELOG.md) from the fragments, or (None, changelog) when none of them gives a number."""
    kinds = {f[1] for f in found}
    if not kinds & {"major", "minor"}:
        return None, changelog
    major, minor = (int(x) for x in version.split("."))
    new = f"{major + 1}.0" if "major" in kinds else f"{major}.{minor + 1}"
    entry = f"## v{new} — {date}\n" + "\n\n".join(f[3] for f in found) + "\n\n"
    first = re.search(r"(?m)^# v", changelog)
    if not first:
        raise SystemExit("CHANGELOG.md has no series heading `# vN.x — …`")
    if "major" in kinds:
        series = next(f[2] for f in found if f[1] == "major")
        return new, changelog[:first.start()] + f"# v{major + 1}.x — {series}\n\n" + entry + changelog[first.start():]
    end = changelog.index("\n", first.start()) + 1
    while changelog[end:end + 1] == "\n":
        end += 1
    return new, changelog[:end] + entry + changelog[end:]


def left(found):
    """On the pull request of Version: a major or minor fragment still there reached main after the branch was built."""
    return [f"changes/{f[0].name} ({f[1]}) is left: it reached main after this pull request was built; the Version workflow updates it"
            for f in found if f[1] != "none"]


def sections(text):
    return set(re.findall(r"(?m)^## v(\d+\.\d+) ", text))


def pull_request(changed, base_changelog, changelog, added_fragment):
    """(errors, warnings) of a pull request other than Version's: changed and added_fragment from git."""
    errors = [f"{f} is written by the Version workflow after the merge: leave it as on main and say what changes in changes/<name>.md"
              for f in LEFT_TO_VERSION if f in changed]
    if "CHANGELOG.md" in changed and sections(changelog) - sections(base_changelog):
        errors.append("CHANGELOG.md: a new version section is written by the Version workflow from changes/<name>.md")
    warnings = []
    if not added_fragment and any(CONTENT.match(f) for f in changed):
        warnings.append("the data or the website change without a fragment in changes/: no version and no CHANGELOG entry will say so (contributing.md)")
    return errors, warnings


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def main(argv):
    found, errors = fragments(ROOT / "changes")
    if argv[:1] == ["check"]:
        if "--strict" in argv:
            errors += left(found)
        warnings = []
        if "--base" in argv:
            base = argv[argv.index("--base") + 1]
            changed = set(git("diff", "--name-only", "--no-renames", base, "HEAD").split())
            added = git("diff", "--name-only", "--diff-filter=A", base, "HEAD", "--", "changes/").split()
            old = git("show", f"{base}:CHANGELOG.md")
            e, warnings = pull_request(changed, old, (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), bool(added))
            errors += e
        for w in warnings:
            print("! " + w)
        if errors:
            print("\n".join("✗ " + e for e in errors), file=sys.stderr)
            return 1
        waiting = ", ".join(f"{f[0].name} ({f[1]})" for f in found) or "none"
        print(f"✓ changes/: fragments waiting for the Version workflow: {waiting}")
        return 0
    if argv[:1] == ["assemble"]:
        if errors:
            print("\n".join("✗ " + e for e in errors), file=sys.stderr)
            return 1
        date = argv[argv.index("--date") + 1] if "--date" in argv else dt.datetime.now(dt.timezone.utc).date().isoformat()
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        new, text = assemble(found, version, (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), date)
        if new is None:
            print(f"{len(found)} fragment(s) of type none wait for the next version", file=sys.stderr)
            return 0
        (ROOT / "VERSION").write_text(new + "\n", encoding="utf-8")
        (ROOT / "CHANGELOG.md").write_text(text, encoding="utf-8")
        for f in found:
            f[0].unlink()
        print(f"version={new}")
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
