# Maintenance

| What | How | When | Who decides |
|---|---|---|---|
| Activity dates, GitHub stars, archived repositories | `scripts/refresh.py` reads the GitHub API, YouTube channel feeds, subreddit feeds and site feeds into `data/metrics.json` | weekly workflow **Refresh metrics**, as a pull request | the maintainer merges |
| Selection of the best (`featured`) | the refresh pull request lists selected entries that are no longer eligible (no activity for 6 months, archived, weak source) | weekly | the maintainer, with a review pass |
| Broken links | lychee over `data/` and the README files | weekly workflow **Links**, opens an issue | the maintainer |
| Statuses on the site | computed from the last activity date at each build | weekly rebuild of **Pages** | automatic |
| Facts, new resources, selection | review pass with a language model, category by category: every entry read at its source, missing resources searched, `featured` reassessed; result as a pull request with a report | each month (5th), and before a submission to the awesome index | the maintainer merges |
| Entries not checked by hand for a year | listed in the refresh pull request | weekly | review pass |

Generated files (`README.md`, `full-list.md`, `site/`) come from `data/` through `scripts/build.py`; the **Check** workflow fails when they are out of date.
