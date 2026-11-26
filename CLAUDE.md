# Working on Awesome LEGO with Claude

Public directory of the brick world: data in `data/*.toml`, README and a bilingual website built by `scripts/build.py` from `site-src/`, published by GitHub Pages. Everything in this repository is in English except the French texts of the data and the website.

- **State, decisions and open items** live outside this repository, in the documents of the maintainer's Claude project (`claude/awesome-lego.md`, `claude/awesome-lego-registre.md`): read them first, and update them at each delivery.
- **How the repository runs**: `MAINTENANCE.md` (workflows, schedules, the maintainer's tasks); rules of the data: `data/SCHEMA.md`; selection rule: `contributing.md` and `site-src/about.json`.
- **One pull request at a time changes `VERSION`, `CHANGELOG.md` and the README image.** Branch from `main`, never from an unmerged branch; merges are squashed by the maintainer, and the title of the pull request (with its version number) becomes the commit on `main`. Work without a visible effect (automation, documents) takes no number; the next version's entry names it.
- **A CHANGELOG entry says what changes in two sentences** (about 250 characters, 550 at most: the build fails beyond); the details go to the pull request.
- **Before pushing**: `python3 scripts/build.py --check`, `python3 -m unittest discover -s tests`, `python3 scripts/check_site.py` with and without `--dejavu` when the website changes, and the image of the README when `VERSION` changes (`python3 scripts/build.py --site-only && python3 scripts/readme_image.py`). Workflows: `actionlint` and `zizmor --offline`.
- A section renamed is renamed in the page title and description too; a value is written once, elsewhere a reference to it.
- **Settled by the maintainer** (not to be raised again without a new reason): the faint grey `--faint` stays at 5.6:1; no installable app (PWA); no visit statistics; Renovate rather than Dependabot for updates; no required review and no stricter ruleset on a one-maintainer repository; contact through GitHub only; a stale README image warns, never fails.
