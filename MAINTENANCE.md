# Maintenance

| What | How | When | Who decides |
|---|---|---|---|
| Activity dates, GitHub stars, statuses on the website | `scripts/refresh.py` reads the GitHub API, YouTube channel feeds, subreddit feeds and site feeds at build time; statuses follow the last activity date | daily rebuild of **Pages**, and at every push to `main` | automatic |
| Data report | the same reading, written to the **Weekly data report** issue: read failures, archived repositories, selected entries no longer eligible (no activity for 6 months, archived, weak source), entries not checked by hand for a year | weekly workflow **Data report** | the maintainer acts on it |
| Broken links | lychee over `data/` and the README | weekly workflow **Links**, opens an issue | the maintainer |
| Facts, new resources, selection of the best (`featured`) | review pass with a language model, category by category: every entry read at its source, missing resources searched, `featured` reassessed; result as a pull request with its CHANGELOG entry | each month (5th), and before a submission to the awesome index | the maintainer merges |
| Versions | `VERSION` and `CHANGELOG.md`; `scripts/changelog.py` drafts the entry from the data changes since the last tag; the **Release** workflow tags `vX.Y` and publishes the GitHub release when `VERSION` changes on `main` | at each merge that changes content or the website: minor (`1.1`); structure or data format: major (`2.0`) | the maintainer |

Generated files (`README.md`, `full-list.md`, `site/`) come from `data/` through `scripts/build.py`; the **Check** workflow fails when they are out of date or when `CHANGELOG.md` has no section for `VERSION`. `data/metrics.json` is a cache of the last reading: the website always uses a fresh one.
