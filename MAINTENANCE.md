# Maintenance

Who does what, and when. Times are UTC. With no action at all, dates, stars and statuses on the website stay current; corrections and additions wait in their pull request.

## At a glance

```mermaid
flowchart LR
  subgraph own["Runs on its own"]
    day["Every day 04:17<br/>Pages: read activity,<br/>rebuild, publish"]
    wed["Wednesday 05:23<br/>Links: test every link"] --> fix["Data fixes<br/>pull request"]
    m4["4th of the month 03:41<br/>Data report: issue"] --> m5["5th, 10:13 Paris time<br/>Review pass: pull request"]
    sec["Monday 05:37 Workflow audit<br/>Tuesday 04:43 Scorecard"]
    tidy["Monday 06:41<br/>Tidy: mechanical fixes"] --> tpr["Tidy<br/>pull request"]
  end
  reno["Renovate<br/>pull requests"] --> merge
  contrib["Contributors<br/>issues, pull requests"] --> merge
  fix --> merge
  m5 --> merge
  tpr --> merge
  merge{{"Maintainer reads<br/>and merges"}} --> main[("main")]
  main --> pub["Pages publishes"]
  main -->|fragments of changes/| ver["Version: pull request vX.Y<br/>(VERSION, CHANGELOG, generated files)"]
  ver --> merge
  main -->|VERSION changed| rel["Release: tag<br/>and release notes"]
```

## Scheduled runs

| Workflow | When (UTC) | Does | Writes |
|---|---|---|---|
| **Pages** | every day 04:17, every push to `main`, after **Preview** | reads activity, builds and publishes the website with the previews | the website; one file a day on branch `history` |
| **Links** | Wednesdays 05:23 | tests every link, from GitHub then from home and office probes | issue **Broken links** |
| **Data fixes** | when **Links** ends, except a dry run | moved addresses, past event dates | pull request **Data fixes** |
| **Version** | after each push to `main` (not one that changes `dev/` alone) | assembles the fragments of `changes/` into the next version | pull request **vX.Y**, when a fragment gives a number |
| **Data report** | the 4th of each month, 03:41 | monthly report for the review | issue **Monthly data report** |
| Review pass (language model) | the 5th of each month, 10:13 Paris time | full review of the data | pull request **Monthly review YYYY-MM** |
| **Workflow audit** | Mondays 05:37 | security audit of the workflows | alerts in the **Security** tab |
| **Scorecard** | Tuesdays 04:43, every push to `main` | score of the repository practices | alerts in the **Security** tab, score at `api.scorecard.dev` |
| **Fuzzing** | Thursdays 03:29 | the fuzz targets of `fuzz/` for 10 minutes: scripts that read third-party pages, feeds and answers | a failed run, the inputs found as an artefact; the corpus kept as an artefact |
| **Tidy** | Mondays 06:41 | fixes that need no judgement: unused Python imports, lossless compression of the PNG files of `media/` (README images excepted) | pull request **Tidy**, only when a file changed |

Started by hand (**Run workflow**): **Pages**, **Links** (with *dry run*), **Data fixes**, **Data report**, **Render**, **Tidy**, **Version** (also rebuilds the generated files without a number), **Release** (notes of the releases), **Fuzzing**.

## On each pull request

| Check | When | What it tells |
|---|---|---|
| **Check** (required) | every pull request, every push to `main` | data valid, the fragment of `changes/`, `VERSION` and the generated files left to **Version**, tests, licences, mechanical guards (`scripts/hygiene.py`) |
| **Render** | when the website, its data or its checks change | the website drawn in a real browser, without defect |
| **Preview** | when the website changes, for a branch of this repository opened by a person | a link to the website of the branch, in a comment |
| **Workflow audit** | when a workflow changes | the workflows are safe |
| **Release** | when `VERSION` or `CHANGELOG.md` changes on `main` (the merge of **vX.Y**) | tag `vX.Y` and the GitHub release; notes of earlier releases set again from `CHANGELOG.md` |

## Maintainer's tasks

The maintainer's working notes (state, decisions, open items, briefs) are in `dev/`, in French; `CLAUDE.md` says how they are kept.

| Task | When | If not done |
|---|---|---|
| Accept **Data fixes** | Wednesdays, after **Links** | old addresses and past dates stay; the next run proposes them again |
| Accept **Tidy** | Mondays, when it opens | unused imports and heavy images stay; the next run proposes them again |
| Read **Broken links** | Wednesdays, when the issue is open | broken links stay until the monthly review |
| Accept **Monthly review YYYY-MM** | after the 5th | corrections and additions wait; merge or close it before the next 5th |
| Accept **vX.Y** | when its entry reads well, after the merges it gathers, once the last run of **Version** has ended | the version, its entry, the README and full-list.md wait; the website is published anyway |
| Keep the review's instructions up to date | when a rule of the data changes | the review writes entries the build refuses |
| Accept Renovate's pull requests | when one opens | tools fall behind, security fixes included |
| Handle security alerts | when GitHub sends one | the flaw stays open |
| Answer contributors | when an issue or a pull request opens | the suggestion waits |
| Renew the key of **Data fixes** | when the workflow warns | its checks wait for **Approve and run workflows** |
| Watch the scheduled runs | after a day without **Pages**, a Wednesday without **Links**, a 4th without **Data report** | dates stop moving, reports are not written |

How, task by task:
- **Data fixes**: read each line; a line in bold says *other site, check the owner* (the address moved to another site); then squash and merge.
- **Broken links**: open in a browser each link of *Broken*, *They answer, but the page is dead* and *Failed twice in a row*; fix or remove the entry by a pull request, or leave it to the review. The folded lists need nothing.
- **Monthly review**: read its summary, the guard line first, then squash and merge.
- **vX.Y**: read the entry of `CHANGELOG.md` in its description (releases are immutable; a fragment is reworded by a pull request to `main`, and the pull request follows), then squash and merge: **Release** tags it.
- **Review instructions**: they live in the scheduled task of the review pass, outside this repository; replace them with the text written for the change.
- **Renovate**: squash and merge when **Check** passes. For MiniSearch, a font or terser, first run `npm ci --ignore-scripts && python3 scripts/vendor.py && python3 scripts/build.py --check` on its branch and commit the files `vendor.py` changed, nothing else (the pull request says so).
- **Security alerts** (**Security** tab, `SECURITY.md`): fix by a pull request, or dismiss a code scanning alert with its reason; for a secret, revoke it at its service first; only the maintainer dismisses a secret scanning alert.
- **Contributors**: before merging, add the French texts and, when it is missing, the fragment `changes/<name>.md`; approve the workflows of an outside contributor after reading the change.
- **Key of Data fixes**: generate a new private key for its GitHub App and store it as the secret `DATA_FIXES_APP_KEY`.
- **Globalping token** (secret `GLOBALPING_TOKEN`, set on 26 Nov 2026): **Links** writes in its log how many tests are left this hour and whether the token was used; a warning means the token is refused: create a new one on [dash.globalping.io](https://dash.globalping.io/) and store it again (**Settings**, **Secrets and variables**, **Actions**).
- **Scheduled runs**: **Actions** tab, filter *Event: schedule*; start a missing one with **Run workflow**. GitHub starts scheduled runs on a best-effort basis, often hours late, and can skip them.

## Workflows in detail

### Pages
- Reads GitHub stars, last pushes and archived flags, YouTube channel feeds, subreddits (public Arctic Shift archive, one at a time: Reddit refuses automated reads) and site feeds (`scripts/refresh.py`).
- After a push, or when started by **Preview**, reuses the measurements of the published website (its `metrics.json`, a few kilobytes) instead of reading again; it reads again only if the website cannot be reached.
- Statuses `active`, `slow` and `inactive` follow the last activity date; past event dates disappear at the next daily run.
- Builds `site/` (`scripts/build.py --site-only`): pages, `details.json` (strengths and weaknesses, read when the browser is idle after the page, so that the search finds them too), `data.json` (every field), `metrics.json` (the measurements alone), feeds of new resources (`feed.xml`, `fr/feed.xml`) and of versions (`changes.xml`).
- Puts under `preview/` the previews of the last successful **Preview** run; runs no branch code; without such a run, or once its artefact is older than 30 days, publishes the website without previews.
- The daily run (or one started by hand without previews) hands the day's measurements to a separate job, the only one allowed to write, which keeps them on the branch `history` (`metrics/YYYY-MM-DD.json`).

### Preview
- Starts when a pull request that changes the website is opened, updated, reopened or closed.
- Files that count as the website: `site-src/`, `scripts/build.py`, `scripts/previews.py`, `media/` (not the image of the README), `data/`, `VERSION`, `CHANGELOG.md`, its own workflow.
- Builds the website of every open pull request of this repository opened by a person: never a fork or a bot; drafts included; 20 at most (`scripts/previews.py`).
- The job can write nowhere. `scripts/previews.py` and `scripts/refresh.py` come from the pull request itself and see the token, read-only; the build of each branch (`scripts/build.py`) runs without it, with the measurements of the published website.
- Each preview, at `preview/<number>/`, carries a banner, a red-tinted sticky header with a red band, a tab title that starts with "Preview #<number>" and `noindex`; a failed build gets an error page.
- Then starts **Pages** and keeps one comment on the pull request with the address. A closed request is no longer listed, so it loses its preview at the next run.
- A preview is served by the same website: anyone can open it, and it shares the browser storage of the published pages (theme, language, new tab). A request opened with the personal token of **Data fixes** counts as a person's.

### Links
- lychee reads `data/`, the README, contributing.md and this file from the machines of GitHub (401, 403, 405 and 429 accepted; loopback addresses skipped).
- Each failure is opened again from 3 Globalping probes on home and office networks (2 in Europe, 1 in North America, else any 3), never from data centres; a redirect is followed for 3 hops at most.
- Broken: fails from every probe that read it (2 at least) and again 90 seconds later. Otherwise it only blocks GitHub. A secure connection refused everywhere is listed apart.
- Dead pages that answer 200 (parked or expired domain, unrelated content, closure notice) are looked for at the address of every open entry.
- Platforms are left out of that search: YouTube, Reddit, GitHub, Facebook, Instagram, Discord, X, TikTok, Flickr, Patreon, Twitch.
- `scripts/links_issue.py` keeps the issue **Broken links** (label `links`): open when a link is broken, a page is dead, or a link failed twice in a row without a verdict; closed otherwise. If lychee writes no report, the issue is left as it is.
- When the hourly limit of Globalping cuts the list, the links of the previous run go first.
- *Dry run* writes the issue body in the run summary, changes no issue and does not start **Data fixes**. `python3 scripts/links_issue.py --sample tests/links-sample.json` reads its yardstick again.

### Data fixes
- `scripts/autofix.py` replaces an address only after a permanent redirect (301 or 308) that ends on a 200 without a query, in 5 hops at most, and removes past `next_date` values; `data/journeys.toml` is left out.
- Two jobs: the first opens the third-party sites and checks the data with read-only rights, and hands its changes over as a patch; the second, the only one allowed to write, runs no script of the repository. Before applying the patch, in a step without any token, a check written in the workflow refuses anything but plain edits of files already tracked as regular files (`data/<name>.toml` alone): no binary patch, no file created, deleted, renamed or linked, no change of mode, 1 MB at most (`tests/test_fixes_workflow.py` runs it against hostile patches). The token comes in only at the step that commits, pushes and opens the pull request, whose body starts with the verified list of changed files and is cut at 60000 characters.
- Recreates the branch `auto/data-fixes` from `main` at each run and opens or updates the pull request **Data fixes** (label `automatic`): a commit added by hand on that branch is lost at the next run.
- The second job writes the fragment `changes/data-fixes-YYYY-MM-DD-HHMM.md` itself, with a fixed text, never taken from the patch (type `none`, see Versions); `README.md` and `full-list.md` are left to **Version**.
- Opens the pull request with its GitHub App (variable `DATA_FIXES_APP_ID`: the app's client ID; secret `DATA_FIXES_APP_KEY`) or, failing that, a personal token (secret `DATA_FIXES_TOKEN`), so that **Check** and **Render** start on their own.

### Tidy
- `scripts/tidy.py` removes unused Python imports (ruff's safe fix) and compresses the PNG files of `media/` without loss (oxipng, text chunks kept); the README images (`media/site-preview*.png`) are left to **Version**.
- Recreates the branch `auto/tidy` from `main` at each run and opens or updates the pull request **Tidy** (label `automatic`) only when a file changed: a commit added by hand on that branch is lost at the next run.
- Opens it with the app or token of **Data fixes**, so that its checks start on their own.
- Runs on Python 3.13, the only one pyoxipng ships wheels for: Renovate keeps the Python of `tidy.yml` below 3.14 (`renovate.json`); raise it, with `tests/requirements-tidy.txt`, once pyoxipng ships wheels for a newer version.

### Data report
- `scripts/refresh.py --month` reads the activity again and writes the issue **Monthly data report** (label `automatic`), read by the review the next day.

| Section | What it lists |
|---|---|
| Guard line | what the previous report listed and is still there |
| Read failures, archived repositories | sources that could not be read, repositories archived |
| Selection no longer eligible | selected entries without activity for 6 months, archived, not active, or on a weak source |
| Not checked for a year | entries to read again |
| Coverage gaps | countries with 3 or more fan communities recognised by LEGO and at most one entry per community |
| Selection check | a selected entry scoring 2 or more below an active one of its group (score out of 7: activity or how recent the check, confidence, sources read) |
| Changes of the month | statuses, archived repositories, entries measured or no longer measured (branch `history`) |
| Links that block GitHub | copied from **Broken links** |
| Reliability, trends | confidence and kinds of sources per category; two windows of 90 days (`scripts/trends.py`) |

- The selection is the rank 1 worldwide of each group.

### Review pass (language model)
- Scheduled task outside this repository; never pushes to `main`.
- Reads every entry at its source and corrects it; adds missing resources; finds feeds (`scripts/discover_feeds.py`); reads `brands`, `funding`, `makers` and `audience` again at the source; reviews the ranks of each group and the needs of "Where to start"; writes the French texts of entries proposed in English.
- Recounts the fan communities per country from the LEGO Fan CoLab directory; renews population figures in January.
- Writes the fragment `changes/review-YYYY-MM.md` (type `minor`) from the draft of `scripts/changelog.py` and opens **Monthly review YYYY-MM**; **Version** gives the number after the merge.

### Check
- Validates `data/`, and the fragments of `changes/` (`scripts/changes.py`: type, one paragraph of 550 characters at most, no bare `@name` or `<`, one major fragment at most); checks that `CHANGELOG.md` has a section for `VERSION`, each paragraph of an entry at most 550 characters (the details belong to the pull request).
- A pull request leaves to **Version** `VERSION`, new sections of `CHANGELOG.md`, `README.md`, `full-list.md`, the category list of the **Add a resource** form and the README images: it fails if it changes them, and fails when it changes `data/` or `site-src/` without adding a fragment (a warning on the branches `renovate/*`, whose bot writes none). Its generated files may then be out of date, whatever `main` holds (a warning); awesome-lint reads the README as the pull request makes it.
- These generated files must be up to date on the pull request of **Version** (no major or minor fragment left either), and on `main` once no fragment waits.
- Checks that this file names every workflow and schedule, and that `data/SCHEMA.md` names every controlled word and backend file.
- Warns, without failing, when the image of the README shows another version.
- `reuse lint` (`REUSE.toml`, `LICENSES/`); unit tests (`tests/`: data, pages, about pages, fragments of `changes/`, links issue, monthly report, previews); awesome-lint as locked in `package-lock.json`; MiniSearch and the fonts of the Brick Vault match their locked packages (`scripts/vendor.py`).
- Mechanical guards (`scripts/hygiene.py`, after the build): ruff and vulture on the Python code (unused imports, functions, classes and variables, unreachable code; `tests/vulture-allow.py` names what the standard library calls); strings of `site-src/strings.json` and fields of the page data that nothing reads; every job with `timeout-minutes` and every pull-request workflow with a `concurrency` group; weight budgets of the pages (per resource, so that the directory may grow) and of the about pages in `tests/budgets.json`, raised only with a reason in the pull request.
- Runs on the latest Python release only; a new push to a pull request cancels its previous run (every push to `main` keeps its own).

### Render
- Builds the website with the measurements of the published website (`scripts/refresh.py --from-site-only`: stars and last activity as published; without them if it cannot be read, never by reading the sources).
- `scripts/check_site.py` opens every view (directory as cards and table, brand mode of an alternative brand and of LEGO, observatory, about page, Brick Vault) in English and French at 1440, 1024, 768, 390 and 320 px, light theme; dark theme at 1440 and 390 px.
- Fails on:
  - a sideways scroll, an element out of its box;
  - a phone, email, date, tag or button label split over two lines, a word split inside itself;
  - overlapping chart labels, a frame inherited by an inner list;
  - a script or security policy error;
  - a word of the strengths or weaknesses that the search does not find;
  - the list drawn in parts (the first cards at once, the others when the browser is idle): empty cards left, or a link to one entry, printing, a search typed at once or the change of language that misses a card not drawn yet;
  - on phones, a search bar on more than two lines, a field under 16 px (a phone zooms into it);
  - a CSS selector that matches nothing in any view and state checked (except data-only runs), unless `tests/css-states.txt` names the state it is for.
- Accessibility (axe-core, WCAG 2.2 A and AA) at 1440 and 390 px, both themes: a guard, not a conformance target (the 13 px studs of the map are accepted).
- First checks itself on `tests/render-fixture.html` and `tests/phone-fixture.html`, where the defects of each check are planted beside sound cases. On failure, the findings are kept 7 days as the artefact `render-findings`.
- A pull request that changes only data and the files generated from it gets a lighter pass (`--data-only`: 1440, 390 and 320 px, light theme, no accessibility; about a fifth of the time of the full checks, measured locally). A push to `main` gets every check.
- Its jobs (layout and accessibility of each width, theme and language, search) are shared between browsers, one per processor, 8 at most (`--jobs`): 1.5 to 2.5 minutes for the run (2 min 18 s measured on 26 Nov 2026 with the about pages).
- The font packages Playwright installs are kept between runs (`actions/cache`, saved from `main` only, a new key each week, with each change of `tests/requirements.txt` and with each runner image): the Ubuntu mirror sometimes served them at 60 kB/s. Kept this week, they are installed directly with `dpkg`, without `apt-get update`, and Playwright checks that nothing it needs is missing; otherwise `--with-deps` as before (`scripts/browser.sh`, which also installs the headless shell alone, the only browser the checks launch). Measured on 27 Nov 2026: the step of the tools takes 11 to 20 s (4 runs, median 12.5 s) against 14 to 33 s before (9 runs, median 24 s); 23 s through `--with-deps`.
- Not a required check (a path filter would leave it pending): its result is read before merging.

### Version
- A pull request says what it changes in `changes/<name>.md` (`contributing.md`, format in `scripts/changes.py`): its type (see Versions), then one paragraph of two sentences; a major one also gives the heading of its series.
- After each push to `main` that leaves a fragment of type `major` or `minor`, assembles the fragments into one entry of `CHANGELOG.md` (one paragraph each, strongest type first), raises `VERSION` by the strongest type, removes the fragments, rebuilds `README.md`, `full-list.md`, the category list of the form and the image of the README, then opens or updates the pull request **vX.Y** (label `automatic`) on the branch `auto/version`, recreated from `main` at each run: a commit added by hand on that branch is lost at the next run.
- Fragments of type `none` alone give no number: they wait, with the generated files, and the entry of the next version cites them. Started by hand, it also rebuilds the generated files without a number (pull request **Generated files**): the repair when `main` fails **Check** with generated files out of date and no fragment waiting.
- After a push that gives no number, closes a pull request **vX.Y** left open (its fragments are gone).
- Two jobs: the build (pip packages, the browser, the fonts kept by **Render**) holds no secret and hands its changes over as a patch. The publication runs no third-party code: it reads the patch before applying it, with the copy of `scripts/version_files.sh` taken from the commit of `main` (only the files Version writes, as plain files: no other path, no rename, no link, no executable), and only then makes the token, in the step that pushes.
- Writes with the app of **Data fixes** or its personal token, so that its checks start on their own; without either it fails with a message: the token of Actions does not push from this job, and the ruleset of `main` lets only the admin role bypass it, so no workflow pushes to `main`.
- Pushes nothing if `main` moved outside `dev/` during the run: the run of the newer push, waiting behind it, publishes. A push of `dev/` alone starts no run, so the run going publishes anyway.
- If the image of the README cannot be taken, the pull request keeps the previous image and says so (a warning, never a failure).
- A pull request, and its preview, shows the version before it: the number exists only once **Version** has run after the merge.
- To write on `main` directly instead (once the app is added to the bypass list of the ruleset): in `version.yml`, push `HEAD:main` in place of `auto/version` and drop the lines of the pull request; Check then needs no exception for `auto/version`.

### Release
- Tags `vX.Y` and publishes the GitHub release with its `CHANGELOG.md` section (`scripts/release_notes.py`); fails if the section is missing, does nothing if the version exists. Releases are immutable: read the entry before merging.
- At each change of `CHANGELOG.md` on `main` (or by hand), the notes of every earlier release are set again to its section when they differ: an entry shortened in the changelog is shortened in its release too.

### Workflow audit and Scorecard
- **Workflow audit**: zizmor reads `.github/workflows/` (dangerous triggers, injections, excessive permissions, unpinned or vulnerable actions) on every pull request or push to `main` that changes a workflow, and Mondays.
- **Scorecard**: OpenSSF Scorecard scores the rules of `main`, pinned dependencies, token permissions, dangerous workflows and security policy; a change of the ruleset is scored at the next run.

### Fuzzing
- Thursdays 03:29, or by hand: ClusterFuzzLite builds the fuzz targets of `fuzz/` in the Python image of OSS-Fuzz (`.clusterfuzzlite/`: Python 3.11, Atheris) and runs them 10 minutes in all, shared between the targets; about 15 minutes with the images, free for a public repository. No run on pull requests, no secret, read-only token.
- Fuzzed, the code that reads what third parties write: feeds (`newest_date` of `scripts/refresh.py`), pages (`classify` of `scripts/links_issue.py`, `find` of `scripts/discover_feeds.py`), redirects of **Data fixes** (`moved` of `scripts/autofix.py`, through the real `http.client`), probes of Globalping (`recheck` and the issue body).
- A finding: an exception the caller does not handle, a result the data or the issue cannot hold, more than 25 seconds or 2.5 GB for one input. The run fails (GitHub mails it) and keeps the input: replay it with `python3 fuzz/<target>.py <file>` (`pip install atheris`), fix the script and add the case to `tests/test_fuzzing.py`.
- The corpus of each target is kept as an artefact from one run to the next (`actions: read` lets the token read the artefacts of earlier runs). The scripts must stay readable by Python 3.11, the version of the image. The image is pinned by digest; it is rebuilt upstream every day, and Renovate renews the digest once a month, on the 1st, in one pull request. The images that the actions of ClusterFuzzLite start themselves (`base-runner`, its builders) follow their `v1` tag, out of reach of Renovate: accepted, since the job holds no secret and only reads.

### Renovate
- Proposes the latest version of the workflows' actions (grouped in one pull request), Python, Node, the tools of the checks, MiniSearch, terser and the fonts, 3 days after it is published, at once for a security fix.
- Refreshes `package-lock.json` once a week (lock file maintenance, Monday before 04:00), for the indirect npm packages that would otherwise move only with a direct one. Renovate raises it without its own 3-day wait, which a lock file without a publication date would never pass; npm keeps the delay itself: `.npmrc` sets `min-release-age=3`, so the new lock holds no version younger than 3 days, and `renovate.json` asks for npm 11.10 or later, the first that reads it. To go back: remove `lockFileMaintenance`, `constraints` and `.npmrc`.
- The Python tools of the checks are locked with their hashes (`tests/*.in`, compiled by `uv pip compile --generate-hashes` into `tests/*.txt`, installed with `--require-hashes --only-binary=:all:`, so no package runs a build script at installation); Renovate compiles the lock again.

## The website

- Generated, never edited by hand: `README.md`, `full-list.md`, the category list of `.github/ISSUE_TEMPLATE/add-resource.yml` and `site/` (not kept in git), all from `data/` by `scripts/build.py`; the files kept in git are committed by **Version**, the website is built by **Pages**.
- `data/backend/` holds figures used by the website but listed nowhere as entries (fan communities per country, population), each with its source and date. `data/metrics.json` is the last reading, written by `scripts/refresh.py` where it runs and not kept in git: a copy in the repository would only grow old (the published one is the reference).
- The website calls no outside service: the page reads only its own `details.json` (`connect-src 'self'` in `scripts/build.py`).
- Every page shares the header (`site-src/header.html`, `header.js`) and the footer (`site-src/footer.html`).
- About pages (`site-src/about.html`, texts in `about.json`, styles in `about.css`; built as `site/about/` and `site/fr/about/`): what the directory is, how it is made, why a selection, how to take part. Their figures come from the data; their texts restate this file and contributing.md in plain words, so a change of the schedule, the method or the criteria goes into `site-src/about.json` in the same pull request.
- The page draws the first cards of the directory at once and the others while the browser is idle, or as their category nears the screen; the search index is built the same way once `details.json` is read. Back, the change of language, printing and Ctrl or Cmd+F draw every card first; a link to one entry (`#entry=`) draws its category and those above it. A card not drawn yet is empty and hidden from screen readers.
- Addresses of former views (`#findings`, `#out`, `#agenda`, `#near-me`) and of the former filter `crit=fr` still lead to their place, until the date written beside them in `site-src/app.js`.
- Speed: `python3 scripts/measure_speed.py [--runs 5] [--json out.json]` loads both home pages of the built website (`site/`) as a slow phone would (processor slowed 4 times, slow 4G, gzip, empty cache, 390 px) and prints the medians: time until the list is shown, longest task and blocking time until then, then the longest task while the page settles, at the first focus of the search field and at the first search. The rule (decision of 24 Nov 2026): a change made for speed is kept only if it gains 10 % at least, on the slower of the two pages, on the measure it aims at (the time until the list for the first display; otherwise the longest task of the moment it is for: the first focus, the first search, the arrival by `--hash '#entry=<id>'`); the pull request gives the figures before and after.
- The Brick Vault (`site-src/vault.html`, built as `site/vault/`): an English-only easter egg opened by the Konami code from any page, with its own fonts (`media/fonts/`, SIL Open Font License) and security policy. Hints: arrows in the footer, a comment and a console message, a search suggestion, the logo hopping as the code is typed.

## Versions

- Types of a fragment of `changes/` (the one definition; elsewhere a reference to it): `minor` (`4.1`) for every merge that changes content or the website; `major` (`5.0`) for a change of structure or data format; `none` for activity data, automation, documents or the README alone. Exception: **Data fixes** writes `none` although it corrects content (moved addresses, past dates), so that its weekly pull request gives no number of its own.
- Each pull request gives its type in its fragment of `changes/`; the number lives in `VERSION` and `CHANGELOG.md`, written by **Version** with the image of the README; **Release** tags it at the merge of **vX.Y**.
