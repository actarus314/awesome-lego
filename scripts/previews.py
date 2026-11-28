"""Previews of the open pull requests, so that the owner sees a change on the website before merging it.

Usage: python3 scripts/previews.py OUT   (run by the Preview workflow; standard library only)

Builds the open pull requests whose branch is in this repository (never a fork; OUT/<number>/), each merged with
main as its merge will publish it (the branch alone when it conflicts with main), its fragments assembled as Version
will (scripts/changes.py assemble: the number and the entry its merge gives), with the merged scripts and the
measurements of the published website, every page marked: a banner that says it is a preview and the number its
merge gives, and `noindex` for search engines. The Preview workflow runs again when main moves, so the number stays
right. OUT/index.html lists the previews. The earlier commits of a pull request that change the website stay
reachable too, each built the same way (merged with main as it is now): OUT/<number>/c/<commit>/, listed by
OUT/<number>/c/, the last MAX_COMMITS of them, the head included; a commit whose website is the same as the one
before it (notes, tests, workflows) gets none. A branch whose build fails gets a page
that says so; the others go on. On a pull_request event, this script and refresh.py come from the pull request itself
and see GH_TOKEN, read-only, in a job that can write nowhere; the build of each branch (build.py) runs in a process
without the token. The Pages workflow only fetches the result (see .github/workflows/preview.yml and pages.yml).
A closed pull request is no longer listed, so the next run drops its preview. At most MAX targets."""
import hashlib
import html
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build  # noqa: E402  the address of the website, written once

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPO = os.environ.get("GITHUB_REPOSITORY", "actarus314/awesome-lego")
PAGES = build.PAGES
MAX = 20   # previews built per run: beyond, the oldest open requests go without
MAX_COMMITS = 10   # commits kept per pull request, the head included (maintainer, 28 Nov 2026)
MAX_EARLIER = 50   # earlier commits built per run, all pull requests together: (MAX + MAX_EARLIER) × about 4 MB stays near 300 MB
BUDGET = 12 * 60   # seconds of the run after which no earlier commit is built (the job stops at 20 minutes; the heads come first)
SITE = ("site-src/", "scripts/build.py", "scripts/changes.py", "media/", "data/", "changes/", "VERSION", "CHANGELOG.md")   # what a commit changes the website with
BANNER = {"en": "Preview of {what} (commit {sha}{merged}){gives}: not the published website.",
          "fr": "Aperçu de {what} (commit {sha}{merged}){gives} : ce n'est pas le site publié."}
GIVES = {"en": ", its merge gives v{v}", "fr": ", sa fusion donne la v{v}"}
NO_NUMBER = {"en": ", its merge gives no new number", "fr": ", sa fusion ne donne aucun nouveau numéro"}
MERGED = {True: {"en": ", merged with main", "fr": ", fusionné avec main"},
          False: {"en": ", alone: it conflicts with main", "fr": ", seul : en conflit avec main"}}
WHAT = {"en": "pull request #{n}", "fr": "la demande de fusion #{n}"}
LINK = {"en": "Open the pull request", "fr": "Ouvrir la demande"}
TAB = {"en": "Preview", "fr": "Aperçu"}
COMMITS = {"en": "Every commit of the pull request", "fr": "Tous les commits de la demande"}
SIDE = {"en": "Side by side", "fr": "Côte à côte"}


def mark(page, n, sha, url, merged=True, version=None, commits=None):
    """A built page marked as a preview: `noindex` in its head, a banner at the top of its body (styles inline, no script:
    the page's security policy allows inline styles and only the scripts it lists). version: the number its merge gives,
    "" for none, None when unknown (a failed build); commits: the address of the list of the commits, when there is one."""
    lang = "fr" if re.search(r'<html[^>]*\blang="fr"', page) else "en"
    gives = "" if version is None else GIVES[lang].format(v=version) if version else NO_NUMBER[lang]
    banner = (f'<div role="note" style="position:relative;z-index:100;background:#7a1f1f;color:#fff;font:600 14px system-ui,sans-serif;'
              f'padding:8px 14px;text-align:center">{html.escape(BANNER[lang].format(what=WHAT[lang].format(n=n), sha=sha, merged=MERGED[merged][lang], gives=gives))} '
              f'<a href="{html.escape(url)}" style="color:#fff">{LINK[lang]}</a>'
              + (f' · <a href="{html.escape(commits)}" style="color:#fff">{COMMITS[lang]}</a>'
                 f' · <a href="{html.escape(re.sub(r"c/$", "compare/", commits))}" style="color:#fff">{SIDE[lang]}</a>' if commits else "") + '</div>')
    # the banner scrolls away with the page; the sticky header stays red-tinted with a red band, and the tab title says it
    keep = ('<style>header.top,#vault header{background:color-mix(in srgb,#c62828 16%,color-mix(in srgb,var(--bg) 88%,transparent))!important;'
            'box-shadow:inset 0 -4px 0 #c62828}</style>')
    page = re.sub(r"(<head[^>]*>)", lambda m: m.group(1) + '<meta name="robots" content="noindex, nofollow">' + keep, page, count=1)
    tag = html.escape(f"{TAB[lang]} #{n} · ")
    if not re.search(r"<title[^>]*>\s*" + re.escape(TAB[lang]), page):  # a page of a failed build already says it
        page = re.sub(r"(<title[^>]*>)", lambda m: m.group(1) + tag, page, count=1)
    return re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + banner, page, count=1)


PAGE = "font:16px/1.5 system-ui,sans-serif;margin:0;padding:32px clamp(16px,4vw,48px)"   # the pages of this script: no width cap on text (rule of the maintainer)


def index(previews):
    """OUT/index.html: the list of the previews, newest pull request first."""
    def row(p):
        if p.get("unchanged"):
            return f'<li>#{p["n"]} {html.escape(p["title"])} · {p["sha"]} · changes nothing on the published website: no preview · <a href="{html.escape(p["url"])}">on GitHub</a></li>'
        return (f'<li><a href="{p["n"]}/">#{p["n"]}</a> {html.escape(p["title"])} · {p["sha"]}{" · build failed" if p["failed"] else ""}'
                f' · <a href="{p["n"]}/c/">its commits</a> · <a href="{p["n"]}/compare/">side by side</a> · <a href="{html.escape(p["url"])}">on GitHub</a></li>')
    rows = "".join(row(p) for p in sorted(previews, key=lambda p: -p["n"]))
    return ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="robots" content="noindex, nofollow">'
            '<meta name="viewport" content="width=device-width"><title>Previews · Awesome LEGO</title></head>'
            f'<body style="{PAGE}"><h1>Previews</h1><ul>{rows or "<li>No open pull request.</li>"}</ul>'
            f'<p><a href="{PAGES}">Published website</a></p></body></html>')


def api(path):
    token = os.environ.get("GH_TOKEN", "")
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}{path}",
                                 headers={"Accept": "application/vnd.github+json", **({"Authorization": f"Bearer {token}"} if token else {})})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if attempt == 2 or e.code < 500:
                raise
        except urllib.error.URLError:
            if attempt == 2:
                raise
        time.sleep(10 * (attempt + 1))


def targets():
    """What to preview: the open pull requests of this repository's branches."""
    out = []
    for p in api("/pulls?state=open&per_page=50") or []:
        if p["head"]["repo"] and p["head"]["repo"]["full_name"] == REPO:
            out.append({"n": p["number"], "sha": p["head"]["sha"], "title": p["title"], "url": p["html_url"]})
    return out[:MAX]


def merge_with_main(wt, sha):
    """In the worktree wt, on main: merge sha as its merge will publish it; True if merged, False (wt on sha alone) if it
    conflicts with main or shares no history with it within the commits fetched."""
    git = ["git", "-c", "user.name=preview", "-c", "user.email=preview@invalid"]
    if subprocess.run([*git, "merge", "-q", "--no-edit", "--no-ff", sha], cwd=wt, capture_output=True, timeout=120).returncode == 0:
        return True
    subprocess.run([*git, "merge", "--abort"], cwd=wt, capture_output=True, timeout=60)
    subprocess.run(["git", "checkout", "-q", "--detach", sha], cwd=wt, check=True, timeout=120)
    return False


def digest(site):
    """A fingerprint of a built website: two commits with the same one show the same thing."""
    h = hashlib.sha256()
    for f in sorted(x for x in site.rglob("*") if x.is_file() and not x.is_symlink()):
        h.update(f.relative_to(site).as_posix().encode() + b"\0" + f.read_bytes() + b"\0")
    return h.hexdigest()


def fetch(sha, cwd=ROOT, remote="origin"):
    """main and sha with their whole history (12 MB, about a second, measured on 28 Nov 2026): the merge base, the
    branch's commits and the numbers of `changes.py assemble` then never depend on a depth. The checkout of the job
    is one commit deep: the first call fetches the rest (`--unshallow`), the next ones only what is new. A depth
    (`--depth=200`) failed on a run started by a push to main: the checkout holds main one commit deep and a depth
    does not deepen a commit already there, so every preview rebuilt after a merge was built alone (28 Nov 2026)."""
    refs = ["+refs/heads/main:refs/remotes/origin/main", sha]
    shallow = subprocess.run(["git", "rev-parse", "--is-shallow-repository"], cwd=cwd, capture_output=True, text=True).stdout.strip() == "true"
    subprocess.run(["git", "fetch", "-q", *(["--unshallow"] if shallow else []), remote, *refs], cwd=cwd, check=True, timeout=300)


def history(sha, cwd=ROOT, main="refs/remotes/origin/main"):
    """The commits of the branch since it left main, oldest first, that change the website (SITE), the head always
    last; at most MAX_COMMITS. Merges of main into the branch are followed on the branch's side only. Without a merge
    base within the commits fetched, the head alone: never commits of main taken for the branch's."""
    base = subprocess.run(["git", "merge-base", main, sha], cwd=cwd, capture_output=True, text=True).stdout.strip()
    if not base:
        return [sha]
    commits = subprocess.run(["git", "rev-list", "--reverse", "--first-parent", f"{base}..{sha}"], cwd=cwd, capture_output=True, text=True, check=True).stdout.split()
    keep = []
    for c in commits[:-1]:
        files = subprocess.run(["git", "diff", "--name-only", f"{c}^1", c], cwd=cwd, capture_output=True, text=True).stdout.split()
        if any(f.startswith(SITE) for f in files):
            keep.append(c)
    return (keep + [sha])[-MAX_COMMITS:]


def fold(rows):
    """The commits to keep, oldest first, from the builds of a pull request (rows: sha, digest, head; the head last):
    a commit whose website is the same as the one kept before it goes (its sha joins `folded` of the one kept); when
    the head is the same as the earlier commits just before it, they go too, and the head names the first of them as
    the commit that made its website (made)."""
    kept = []
    for r in rows:
        if kept and r["digest"] == kept[-1]["digest"]:
            if r["head"]:
                same = kept.pop()
                folded = [same["sha"], *same.get("folded", [])]
                while kept and kept[-1]["digest"] == r["digest"]:
                    same = kept.pop()
                    folded = [same["sha"], *same.get("folded", []), *folded]
                kept.append({**r, "made": same.get("made", same["sha"]), "folded": folded})
            else:
                kept[-1] = {**kept[-1], "folded": [*kept[-1].get("folded", []), r["sha"]]}
            continue
        kept.append(r)
    return kept


def note_of(r, notes_by_sha):
    """The note of a kept commit: its own, else that of the commit that made its website, else of a commit folded into it."""
    return next((notes_by_sha[c] for c in [r["sha"], r.get("made"), *r.get("folded", [])] if c and notes_by_sha.get(c)), "")


def site_of(sha, wt, env):
    """In the new worktree wt: sha merged with main, its fragments assembled, built. (merged, version)."""
    main_sha = subprocess.run(["git", "rev-parse", "refs/remotes/origin/main"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    subprocess.run(["git", "worktree", "add", "-q", "--detach", str(wt), main_sha], cwd=ROOT, check=True, timeout=120)
    merged = merge_with_main(wt, sha)
    done = subprocess.run([sys.executable, "scripts/changes.py", "assemble"], cwd=wt, env=env, capture_output=True,
                          text=True, check=True, timeout=120).stdout  # VERSION and CHANGELOG.md as Version will write them
    version = re.sub(r"^version=", "", done.strip()) if done.startswith("version=") else ""
    metrics = ROOT / "data" / "metrics.json"
    if metrics.exists():
        shutil.copy(metrics, wt / "data" / "metrics.json")  # measurements of the published website, read by the step before
    subprocess.run([sys.executable, "scripts/build.py", "--site-only"], cwd=wt, env=env, check=True, timeout=300)
    return merged, version


def place(site, dest, n, sha, url, merged, version, commits):
    """The built website copied to dest, every page of it marked (not those already under dest, such as c/)."""
    shutil.copytree(site, dest, symlinks=True, dirs_exist_ok=True)  # the head goes around the folder c/ of the earlier commits
    pages = [dest / x.relative_to(site) for x in site.rglob("*.html")]
    for f in [f for f in dest.rglob("*") if f.is_symlink()]:
        f.unlink()  # a link would publish a file of the machine
    for f in pages:
        if f.exists():
            f.write_text(mark(f.read_text(encoding="utf-8"), n, sha[:7], url, merged, version, commits), encoding="utf-8")


def notes(sha, cwd=ROOT, main="refs/remotes/origin/main"):
    """What to compare, from the trailers `Preview-compare:` of the branch's commit messages (the last paragraph, with
    Co-Authored-By): `Preview-compare: <note>` marks its own commit; `Preview-compare: <commit> <note>` marks an earlier
    commit (pushed commits are never rewritten), by a prefix of at least 7 characters that names one commit only.
    {full sha: note}, a later trailer replacing an earlier one; a commit marked without a note gets "to compare"."""
    base = subprocess.run(["git", "merge-base", main, sha], cwd=cwd, capture_output=True, text=True).stdout.strip()
    log = subprocess.run(["git", "log", "--reverse", "--first-parent", "-n", "200",
                          "--format=%H%x00%(trailers:key=Preview-compare,valueonly,unfold,separator=%x01)%x1e",
                          f"{base}..{sha}" if base else sha], cwd=cwd, capture_output=True, text=True).stdout
    entries = [e.split("\0", 1) for e in log.split("\x1e") if "\0" in e]
    shas = [own.strip() for own, _ in entries]
    out = {}
    for own, values in entries:
        for v in (x.strip() for x in values.split("\x01")):
            if not v:
                continue
            first, _, rest = v.partition(" ")
            hits = [c for c in shas if c.startswith(first.lower())] if re.fullmatch(r"[0-9a-fA-F]{7,40}", first) else []
            target, note = (hits[0], rest.strip()) if len(hits) == 1 else (own.strip(), v)
            out[target] = note or "to compare"
    return out


def commit_list(n, url, rows):
    """OUT/<number>/c/index.html: the commits of the pull request that have a preview, oldest first, newest last; those
    to compare (a note, see notes()) in bold with their note; the published website as the reference."""
    total = len(rows)

    def line(i, r):
        made, head = r.get("made"), r["sha"][:7]
        sha = (made or r["sha"])[:7]
        where = "newest" if i == total else "oldest" if i == 1 else ""
        text = (f'{i} of {total}{" (" + where + ")" if where else ""} · <a href="{html.escape(r["href"])}">{sha}</a> · {html.escape(r["subject"])}'
                f'{f" (head {head}: same website)" if made else ""}')
        note = r.get("note")
        return f'<li><b>{text}</b><br>To compare: {html.escape(note)}</li>' if note else f"<li>{text}</li>"
    return ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="robots" content="noindex, nofollow">'
            f'<meta name="viewport" content="width=device-width"><title>Preview #{n}: commits · Awesome LEGO</title></head>'
            f'<body style="{PAGE}"><h1>Pull request #{n}: one preview per commit</h1>'
            f'<p>Oldest first, newest last: the commits that change the website, each merged with main as it is now ({MAX_COMMITS} at most). '
            'In bold, the versions to compare. French pages under <code>fr/</code> of each.</p>'
            f'<p>Reference: <a href="{PAGES}">the published website</a> · <a href="../compare/">all of them side by side</a></p>'
            f'<ol style="padding-left:1.2em">{"".join(line(i, r) for i, r in enumerate(rows, 1))}</ol>'
            f'<p><a href="{html.escape(url)}">The pull request on GitHub</a> · <a href="../../">All previews</a></p></body></html>')


def compare_page(n, rows):
    """OUT/<number>/compare/index.html: versions side by side, 2 frames at first, 5 at most, each with its version
    (the published website or a commit) and its note on one line of fixed height; a simulated width, scaled to fit;
    scrolling and the address followed by the other frames unless turned off; the choice kept in the address (#v=…)."""
    versions = [{"id": "published", "label": "Published website", "root": "../../../", "note": ""}]
    for i, r in enumerate(rows, 1):
        sha = (r.get("made") or r["sha"])[:7]
        versions.append({"id": sha, "label": f'{i} of {len(rows)}{" (newest)" if r["head"] else ""} · {sha} · {r["subject"]}',
                         "root": "../" if r["head"] else f"../c/{sha}/", "note": r.get("note", "")})
    data = json.dumps(versions, ensure_ascii=False).replace("<", "\\u003c")
    return COMPARE.replace("{{N}}", str(n)).replace("{{DATA}}", data)


COMPARE = (pathlib.Path(__file__).resolve().parent / "compare.html").read_text(encoding="utf-8")   # the page, its data filled in by compare_page()


def log_of(c):
    """Date and subject of a commit."""
    out = subprocess.run(["git", "log", "-1", "--format=%cs%x00%s", c], cwd=ROOT, capture_output=True, text=True).stdout.strip().split("\0")
    return (out[0], out[1]) if len(out) == 2 else ("", out[-1])


def one(p, c, dest, listed, env):
    """Commit c of pull request p built and placed at dest; its digest, or None if it did not build (nothing left at dest)."""
    with tempfile.TemporaryDirectory() as tmp:
        wt = pathlib.Path(tmp) / "branch"
        try:
            merged, version = site_of(c, wt, env)
            d = digest(wt / "site")
            place(wt / "site", dest, p["n"], c, p["url"], merged, version, listed)
            return d
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as e:
            print(f"::warning::preview of #{p['n']} at {c[:7]} not built: {e}")
            if dest.name != str(p["n"]):
                shutil.rmtree(dest, ignore_errors=True)  # no unmarked copy of an earlier commit stays
            return None
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", str(wt)], cwd=ROOT, check=False)


def published(env):
    """The fingerprint of main's website as it stands, built the same way as the previews (once per run)."""
    if "main" not in PUBLISHED:
        with tempfile.TemporaryDirectory() as tmp:
            wt = pathlib.Path(tmp) / "main"
            try:
                main_sha = subprocess.run(["git", "rev-parse", "refs/remotes/origin/main"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
                site_of(main_sha, wt, env)
                PUBLISHED["main"] = digest(wt / "site")
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as e:
                print(f"::warning::main not built, every pull request gets its preview: {e}")
                PUBLISHED["main"] = None
            finally:
                subprocess.run(["git", "worktree", "remove", "--force", str(wt)], cwd=ROOT, check=False)
    return PUBLISHED["main"]


PUBLISHED = {}


def heads(p, out, env):
    """First pass: the head of pull request p, as before; the commits it has to show next. True if the head built.
    A head whose website is the same as main's gets no preview (p["unchanged"]): nothing to see."""
    n, sha = p["n"], p["sha"]
    try:
        fetch(sha)
        p["commits"] = history(sha)
        p["notes"] = notes(sha)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as e:
        print(f"::warning::commits of #{n} not read: {e}")
        p["commits"], p["notes"] = [sha], {}
    listed = f"{PAGES}preview/{n}/c/" if len(p["commits"]) > 1 else None
    p["digest"] = one(p, sha, out / str(n), listed, env)
    if p["digest"] is not None and p["digest"] == published(env):
        shutil.rmtree(out / str(n), ignore_errors=True)
        p["unchanged"] = True
        return True
    if p["digest"] is None:
        dest = out / str(n)
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "index.html").write_text(mark(f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Preview {n}</title></head>'
                                              f'<body><p style="padding:20px">The website of this branch did not build: see the run of the Preview workflow.</p></body></html>',
                                              n, sha[:7], p["url"], commits=listed), encoding="utf-8")
    return p["digest"] is not None


def earlier(p, out, env, left):
    """Second pass: the earlier commits of pull request p, while `left()` allows; then the list of its commits and the
    page that puts them side by side."""
    n, sha = p["n"], p["sha"]
    if p.get("unchanged"):
        return
    listed = f"{PAGES}preview/{n}/c/"
    rows = []
    for c in p["commits"][:-1]:
        if not left():
            print(f"::warning::earlier commits of #{n} not all built: budget of the run or of MAX_EARLIER reached")
            break
        d = one(p, c, out / str(n) / "c" / c[:7], listed, env)
        if d is not None:
            rows.append({"sha": c, "digest": d, "head": False})
    rows.append({"sha": sha, "digest": p["digest"], "head": True})
    kept = fold(rows)
    for r in rows:
        if not r["head"] and r not in kept:
            shutil.rmtree(out / str(n) / "c" / r["sha"][:7], ignore_errors=True)
    for r in kept:
        made = r.get("made", r["sha"])
        r["date"], r["subject"] = log_of(made)
        r["href"] = "../" if r["head"] else f'{r["sha"][:7]}/'
        r["note"] = note_of(r, p.get("notes", {}))
    shown = {c for r in kept for c in [r["sha"], r.get("made"), *r.get("folded", [])] if c}
    for c in p.get("notes", {}):
        if c not in shown:
            print(f"::warning::#{n}: a Preview-compare note marks {c[:7]}, which has no preview of its own (it does not change the website)")
    (out / str(n) / "c").mkdir(parents=True, exist_ok=True)
    (out / str(n) / "c" / "index.html").write_text(commit_list(n, p["url"], kept), encoding="utf-8")
    (out / str(n) / "compare").mkdir(parents=True, exist_ok=True)
    (out / str(n) / "compare" / "index.html").write_text(compare_page(n, kept), encoding="utf-8")


def main():
    out = pathlib.Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    began = time.monotonic()
    env = {k: v for k, v in os.environ.items() if k not in ("GH_TOKEN", "GITHUB_TOKEN")}  # the branch's code never sees a token
    previews, built = [], [0]
    for p in targets():  # every head first: an earlier commit never costs a pull request its preview
        ok = heads(p, out, env)
        previews.append(p | {"failed": not ok})
        print(f"{'✓' if ok else '✗'} preview of {p['n']} ({p['sha'][:7]}){': same website as main, none' if p.get('unchanged') else ''}")

    def left():
        built[0] += 1
        return built[0] <= MAX_EARLIER and time.monotonic() - began < BUDGET
    for p in previews:
        earlier(p, out, env, left)
    (out / "index.html").write_text(index([{**p, "sha": p["sha"][:7]} for p in previews]), encoding="utf-8")
    if os.environ.get("GITHUB_OUTPUT"):
        unchanged_output(previews, os.environ["GITHUB_OUTPUT"])


def unchanged_output(previews, path):
    """The pull requests without a preview, for the comment of the workflow: numbers only."""
    with open(path, "a", encoding="utf-8") as f:
        f.write("unchanged=" + " ".join(str(int(p["n"])) for p in previews if p.get("unchanged")) + "\n")


if __name__ == "__main__":
    main()
