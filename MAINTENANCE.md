# Maintenance

Who does what, when and how. Times are UTC. Only the **Maintainer** rows wait for a person.

| Who | When | What | How |
|---|---|---|---|
| GitHub Actions: **Pages** | daily at 04:17, and at every push to `main` | rebuilds and publishes the website | `scripts/refresh.py` reads GitHub stars, last commits and archived flags, YouTube channel feeds, subreddit feeds and site feeds; statuses (active, slowing, inactive) follow the last activity date; `scripts/build.py --site-only` builds `site/` |
| GitHub Actions: **Data report** | Mondays at 03:41 | data report | opens or updates the **Weekly data report** issue: read failures, archived repositories, selected entries no longer eligible (no activity for 6 months, archived, weak source), entries not checked by hand for a year |
| GitHub Actions: **Links** | Wednesdays at 05:23 | link check | lychee over `data/` and the README; opens a **Broken links** issue when a link fails |
| GitHub Actions: **Check** | every pull request and every push | validation | validates `data/`, checks that `README.md` and `full-list.md` are up to date and that `CHANGELOG.md` has a section for `VERSION`, runs awesome-lint; a pull request cannot be merged without it |
| GitHub Actions: **Release** | when `VERSION` changes on `main` | release | tags `vX.Y` and publishes the GitHub release with its `CHANGELOG.md` section |
| Review pass (language model) | the 5th of each month at 10:13 Paris time | full review | every entry read at its source, corrected, missing resources added, selection of the best (`featured`) reassessed from the weekly report; minor version bumped, `CHANGELOG.md` entry written from `scripts/changelog.py`; opens a **Monthly review vX.Y** pull request, never pushes to `main` |
| Renovate | when a tool has a new version | updates the workflows | opens a pull request, tested by **Check** |
| Contributors | any time | suggest or fix | issue forms (**Add a resource**, **Fix an entry**) or a pull request from a fork; workflows of outside contributors wait for the maintainer's approval |
| **Maintainer** | after the 5th of each month | accept the review | read the summary of the **Monthly review** pull request, then squash and merge; website and release follow |
| **Maintainer** | when Renovate opens a pull request | tool update | squash and merge when **Check** passes |
| **Maintainer** | when a contributor opens an issue or a pull request | decide | merge or close a pull request (adding the French texts, `VERSION` and the `CHANGELOG.md` entry); an issue can wait for the next review pass |

The weekly and link issues need no action: the monthly review takes them in. With no action at all, dates, stars and statuses on the website stay current; corrections and additions wait in their pull request.

Versions: minor (`1.1`) for every merge that changes content or the website, major (`2.0`) for a change of structure or data format, none for activity data alone. Generated files (`README.md`, `full-list.md`, `site/`) come from `data/` through `scripts/build.py`. `data/metrics.json` is a local cache of the last reading: the website always reads fresh data.
