#!/usr/bin/env python3
"""Fragments of changes/: what each pull request changes, assembled after the merge into the CHANGELOG.md entry of
the next version by the workflow Version (standard library only).

A pull request never writes VERSION, a CHANGELOG.md section, README.md, full-list.md, the category list of the
"Add a resource" form or the README images: it adds changes/<name>.md (name: lowercase letters, digits and hyphens),
for example

    type: minor

    Website: the about page keeps the place being read when the language changes. Feed: named Awesome LEGO.

The type is major, minor, patch or none, as MAINTENANCE.md defines them (section Versions); a fragment of type none
gives no number and waits, cited by the entry of the next version. A major fragment adds a line `series: <one sentence>` under
its type: the heading of the new series of versions. The text says what changes in two sentences, CHANGELOG_MAX
characters at most (scripts/build.py), with no bare @ (GitHub would notify the account) and no bare < (HTML): both in
backticks.

Usage:
  python3 scripts/changes.py check [--base REF [--branch NAME]]
      every fragment well formed. --base REF (on a pull request: the branch it merges into; what changed since their
      merge base): the pull request leaves VERSION, the sections of CHANGELOG.md, the generated files and the README
      images to Version, and fails when it changes the data, the website or the scripts that build it without adding
      a fragment (a warning for the branches renovate/*, whose bot writes none).
  python3 scripts/changes.py assemble [--date YYYY-MM-DD]
      VERSION raised by the strongest type, the entry written at the top of CHANGELOG.md, the fragments removed;
      prints version=X.Y or X.Y.Z (for $GITHUB_OUTPUT), or nothing and changes nothing when nothing gives a number.
      When no fragment gives a number but what the website serves changed since the commit of the current version
      (the last one that changed VERSION: a dependency Renovate raised, a file Tidy rebuilt), a patch whose entry
      says so. Run by Version on main, and by previews.py on each pull request merged with main: the preview shows
      the number and the entry its merge gives. Needs the history back to that commit (a shallow clone: a warning,
      no such patch).

A version is MAJOR.MINOR, or MAJOR.MINOR.PATCH when its patch is not zero: 4.10, then 4.10.1, 4.10.2, then 4.11; a
tag of an earlier version (vX.Y) keeps its name.
"""
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import CHANGELOG_MAX, FILES, ID, README_IMAGES  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TYPES = ("major", "minor", "patch", "none")  # strongest first
NUMBERED = {"major", "minor", "patch"}
SITE_ONLY = "Website: rebuilt with updated dependencies or files, nothing a visitor reads changes."  # the entry of a patch given by --site-changed alone
LEFT_TO_VERSION = ["VERSION", *FILES.values(), *(f"media/{n}" for n in README_IMAGES)]
FORM = ".github/ISSUE_TEMPLATE/add-resource.yml"  # its category list is generated (build.issue_form); the rest of it is written by hand
CONTENT = re.compile(r"^(data|site-src)/|^scripts/(build|refresh|trends)\.py$")  # what a reader sees, or what makes it: a pull
# request that changes it says so in a fragment (type none for a change no page shows)
BOTS = re.compile(r"^renovate/")  # branches of a bot that cannot write a fragment: a warning instead of a failure
SITE = re.compile(r"^(data|site-src|media)/")  # what the website serves (vendored files: site-src/vendor/): changed by a bot
# without fragment, a patch
MENTION = re.compile(r"(?<![\w.`])@[A-Za-z0-9][\w-]*")


def parse(path):
    """(type, series, text) of a fragment, or raises ValueError with what to fix."""
    if not path.is_file():
        raise ValueError("a fragment is a file, not a folder")
    if path.suffix != ".md" or not ID.fullmatch(path.stem):
        raise ValueError("name a fragment <name>.md, with lowercase letters, digits and hyphens")
    lines = path.read_text(encoding="utf-8-sig").strip().splitlines()  # a byte order mark left by an editor is no defect
    m = re.fullmatch(r"type: (\S+)", lines[0].strip()) if lines else None
    if not m or m.group(1) not in TYPES:
        raise ValueError("the first line is `type: major`, `type: minor`, `type: patch` or `type: none`")
    kind, rest, series = m.group(1), lines[1:], None
    if rest and rest[0].startswith("series:"):
        series, rest = rest[0].removeprefix("series:").strip(), rest[1:]
    if kind == "major" and not series:
        raise ValueError("a major fragment says the heading of its series on a second line, `series: <one sentence>`")
    if kind != "major" and series is not None:
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
    bare = re.sub(r"`[^`]*`", "", text + " " + (series or ""))  # what is not code: read as Markdown in the release and the pull request
    if MENTION.search(bare):
        raise ValueError("a bare @name notifies that account in the release and its pull request: write `@name` in backticks, or leave it out")
    if "<" in bare:
        raise ValueError("a bare < opens HTML in the release and its pull request: write `<name>` in backticks")
    return kind, series or "", text


def fragments(folder):
    """[(path, type, series, text)] in the order of the entry (strongest type first, then by name), and the errors."""
    out, errors = [], []
    for p in sorted(folder.iterdir()) if folder.is_dir() else []:
        try:
            out.append((p, *parse(p)))
        except ValueError as e:
            errors.append(f"changes/{p.name}: {e}")
    out.sort(key=lambda f: TYPES.index(f[1]))
    majors = [f[0].name for f in out if f[1] == "major"]
    if len(majors) > 1:  # one version opens one series: the heading of the second would be lost
        errors.append(f"changes/: {len(majors)} major fragments ({', '.join(majors)}): one version opens one series, make the others minor")
    return out, errors


def bump(version, kinds):
    """The next version for these fragment types, or None: X.Y, or X.Y.Z when the patch is not zero."""
    parts = [int(x) for x in version.split(".")]
    if len(parts) not in (2, 3):
        raise SystemExit(f"VERSION {version!r}: MAJOR.MINOR or MAJOR.MINOR.PATCH")
    major, minor, patch = (parts + [0])[:3]
    if "major" in kinds:
        return f"{major + 1}.0"
    if "minor" in kinds:
        return f"{major}.{minor + 1}"
    if "patch" in kinds:
        return f"{major}.{minor}.{patch + 1}"
    return None


def site_changed(paths):
    """True if one of these paths changes what the website serves (the README images are not served)."""
    return any(SITE.match(p) and not p.startswith(tuple(f"media/{n}" for n in README_IMAGES)) for p in paths)


def assemble(found, version, changelog, date, site_changed=False):
    """(new version, new CHANGELOG.md) from the fragments, or (None, changelog) when none of them gives a number."""
    kinds = {f[1] for f in found}
    texts = [f[3] for f in found]
    if not kinds & NUMBERED and site_changed:
        kinds, texts = {"patch"}, [SITE_ONLY, *texts]
    new = bump(version, kinds)
    if new is None:
        return None, changelog
    major = int(version.split(".")[0])
    entry = f"## v{new} — {date}\n" + "\n\n".join(texts) + "\n\n"
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


def sections(text):
    return set(re.findall(r"(?m)^## v(\d+\.\d+(?:\.\d+)?) ", text))


def categories(form):
    """The category list of the "Add a resource" form, the part build.py generates."""
    m = re.search(r"label: Category\n      options:\n((?:        - [^\n]*\n)+)", form)
    return m.group(1) if m else ""


def pull_request(changed, base, head, added_fragment, branch=""):
    """(errors, warnings) of a pull request other than Version's. changed and added_fragment come from git; base and
    head map CHANGELOG.md and the form to their text at the merge base and in the pull request."""
    errors = [f"{f} is written by the Version workflow after the merge: leave it as on main and say what changes in changes/<name>.md"
              for f in LEFT_TO_VERSION if f in changed]
    if "CHANGELOG.md" in changed and sections(head["CHANGELOG.md"]) - sections(base["CHANGELOG.md"]):
        errors.append("CHANGELOG.md: a new version section is written by the Version workflow from changes/<name>.md")
    if FORM in changed and categories(head[FORM]) != categories(base[FORM]):
        errors.append(f"{FORM}: its category list is written by the Version workflow from data/ (the rest of the form may change)")
    warnings = []
    if not added_fragment and any(CONTENT.match(f) for f in changed):
        say = "the data or the website change without a fragment: add changes/<name>.md (contributing.md), or no version and no CHANGELOG entry will say so"
        (warnings if BOTS.match(branch) else errors).append(say)
    return errors, warnings


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def site_changed_since_version():
    """True if what the website serves changed since the commit of the current version (the last one that changed
    VERSION, which Release tags); False, with a warning, when the history does not reach it (a shallow clone)."""
    try:
        base = git("log", "-1", "--format=%H", "--", "VERSION").strip()
        shallow = ROOT / git("rev-parse", "--git-path", "shallow").strip()  # the commits where a shallow history stops: one of
        # them seems to add every file, VERSION included
        if base and base not in (shallow.read_text(encoding="utf-8").split() if shallow.exists() else []):
            return site_changed(git("diff", "--name-only", "--no-renames", base, "HEAD").split())
    except (subprocess.CalledProcessError, OSError):
        pass
    print("! the history does not reach the commit of the current version: no patch for a website change without fragment", file=sys.stderr)
    return False


def main(argv):
    found, errors = fragments(ROOT / "changes")
    if argv[:1] == ["check"]:
        warnings = []
        if "--base" in argv:
            base = git("merge-base", argv[argv.index("--base") + 1], "HEAD").strip()  # what this branch changed, not what the base did since
            branch = argv[argv.index("--branch") + 1] if "--branch" in argv else ""
            changed = set(git("diff", "--name-only", "--no-renames", f"{base}...HEAD").split())
            added = git("diff", "--name-only", "--no-renames", "--diff-filter=A", f"{base}...HEAD", "--", "changes/").split()
            show = lambda f: git("show", f"{base}:{f}")
            e, warnings = pull_request(changed, {f: show(f) for f in ("CHANGELOG.md", FORM)},
                                       {f: (ROOT / f).read_text(encoding="utf-8") for f in ("CHANGELOG.md", FORM)}, bool(added), branch)
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
        moved = site_changed_since_version()
        new, text = assemble(found, version, (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), date, moved)
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
