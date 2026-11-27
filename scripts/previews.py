"""Previews of the open pull requests, so that the owner sees a change on the website before merging it.

Usage: python3 scripts/previews.py OUT   (run by the Preview workflow; standard library only)

Builds the open pull requests whose branch is in this repository (never a fork or a bot; OUT/<number>/), each with
that branch's own scripts and the measurements of the published website, every page marked: a banner that says it is
a preview, and `noindex` for search engines. OUT/index.html lists the previews. A branch whose build fails gets a page
that says so; the others go on. On a pull_request event, this script and refresh.py come from the pull request itself
and see GH_TOKEN, read-only, in a job that can write nowhere; the build of each branch (build.py) runs in a process
without the token. The Pages workflow only fetches the result (see .github/workflows/preview.yml and pages.yml).
A closed pull request is no longer listed, so the next run drops its preview. At most MAX targets."""
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
BANNER = {"en": "Preview of {what} (commit {sha}): not the published website.",
          "fr": "Aperçu de {what} (commit {sha}) : ce n'est pas le site publié."}
WHAT = {"en": "pull request #{n}", "fr": "la demande de fusion #{n}"}
LINK = {"en": "Open the pull request", "fr": "Ouvrir la demande"}
TAB = {"en": "Preview", "fr": "Aperçu"}


def mark(page, n, sha, url):
    """A built page marked as a preview: `noindex` in its head, a banner at the top of its body (styles inline, no script:
    the page's security policy allows inline styles and only the scripts it lists)."""
    lang = "fr" if re.search(r'<html[^>]*\blang="fr"', page) else "en"
    banner = (f'<div role="note" style="position:relative;z-index:100;background:#7a1f1f;color:#fff;font:600 14px system-ui,sans-serif;'
              f'padding:8px 14px;text-align:center">{html.escape(BANNER[lang].format(what=WHAT[lang].format(n=n), sha=sha))} '
              f'<a href="{html.escape(url)}" style="color:#fff">{LINK[lang]}</a></div>')
    # the banner scrolls away with the page; the sticky header stays red-tinted with a red band, and the tab title says it
    keep = ('<style>header.top,#vault header{background:color-mix(in srgb,#c62828 16%,color-mix(in srgb,var(--bg) 88%,transparent))!important;'
            'box-shadow:inset 0 -4px 0 #c62828}</style>')
    page = re.sub(r"(<head[^>]*>)", lambda m: m.group(1) + '<meta name="robots" content="noindex, nofollow">' + keep, page, count=1)
    tag = html.escape(f"{TAB[lang]} #{n} · ")
    if not re.search(r"<title[^>]*>\s*" + re.escape(TAB[lang]), page):  # a page of a failed build already says it
        page = re.sub(r"(<title[^>]*>)", lambda m: m.group(1) + tag, page, count=1)
    return re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + banner, page, count=1)


def index(previews):
    """OUT/index.html: the list of the previews, newest pull request first."""
    rows = "".join(f'<li><a href="{p["n"]}/">#{p["n"]}</a> {html.escape(p["title"])} · {p["sha"]}'
                   f'{" · build failed" if p["failed"] else ""} · <a href="{html.escape(p["url"])}">on GitHub</a></li>'
                   for p in sorted(previews, key=lambda p: -p["n"]))
    return ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="robots" content="noindex, nofollow">'
            '<meta name="viewport" content="width=device-width"><title>Previews · Awesome LEGO</title></head>'
            '<body style="font:16px/1.5 system-ui,sans-serif;max-width:760px;margin:40px auto;padding:0 16px">'
            f'<h1>Previews</h1><ul>{rows or "<li>No open pull request.</li>"}</ul>'
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
        if p["head"]["repo"] and p["head"]["repo"]["full_name"] == REPO and p["user"]["type"] != "Bot":  # dependency and data-fix requests change no page worth looking at
            out.append({"n": p["number"], "sha": p["head"]["sha"], "title": p["title"], "url": p["html_url"]})
    return out[:MAX]


def build(p, out):
    """The website of one branch, built by the branch's own build.py; True if it built."""
    n, sha = p["n"], p["sha"]
    env = {k: v for k, v in os.environ.items() if k not in ("GH_TOKEN", "GITHUB_TOKEN")}  # the branch's code never sees a token
    with tempfile.TemporaryDirectory() as tmp:
        wt = pathlib.Path(tmp) / "branch"
        try:
            subprocess.run(["git", "fetch", "-q", "--depth=1", "origin", sha], cwd=ROOT, check=True, timeout=120)
            subprocess.run(["git", "worktree", "add", "-q", "--detach", str(wt), sha], cwd=ROOT, check=True, timeout=120)
            metrics = ROOT / "data" / "metrics.json"
            if metrics.exists():
                shutil.copy(metrics, wt / "data" / "metrics.json")  # measurements of the published website, read by the step before
            subprocess.run([sys.executable, "scripts/build.py", "--site-only"], cwd=wt, env=env, check=True, timeout=300)
            dest = out / str(n)
            shutil.copytree(wt / "site", dest, symlinks=True)
            for f in [f for f in dest.rglob("*") if f.is_symlink()]:
                f.unlink()  # a link would publish a file of the machine
            for f in dest.rglob("*.html"):
                f.write_text(mark(f.read_text(encoding="utf-8"), n, sha[:7], p["url"]), encoding="utf-8")
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as e:
            print(f"::warning::preview of #{n} not built: {e}")
            dest = out / str(n)
            dest.mkdir(parents=True, exist_ok=True)
            (dest / "index.html").write_text(mark(f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Preview {n}</title></head>'
                                                  f'<body><p style="padding:20px">The website of this branch did not build: see the run of the Preview workflow.</p></body></html>',
                                                  n, sha[:7], p["url"]), encoding="utf-8")
            return False
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", str(wt)], cwd=ROOT, check=False)


def main():
    out = pathlib.Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    previews = []
    for p in targets():
        ok = build(p, out)
        previews.append({**p, "sha": p["sha"][:7], "failed": not ok})
        print(f"{'✓' if ok else '✗'} preview of {p['n']} ({p['sha'][:7]})")
    (out / "index.html").write_text(index(previews), encoding="utf-8")


if __name__ == "__main__":
    main()
