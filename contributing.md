# Contributing

This list aims to be complete, accurate and current. Every entry is checked at its source. Entries carry English and French texts (`_en` and `_fr` fields) because the website is bilingual; a contribution in English only is welcome, the French text is added before merging.

**Suggest without editing files:** open an issue with the [Add a resource](../../issues/new?template=add-resource.yml) or [Fix an entry](../../issues/new?template=fix-entry.yml) form. A maintainer writes the entry.

**Edit the data yourself:**
1. Edit the TOML file of the category in [`data/`](data/), following [`data/SCHEMA.md`](data/SCHEMA.md). `README.md`, `full-list.md` and `data/metrics.json` are generated: do not edit them by hand.
2. Run `python3 scripts/build.py` (Python 3.11 or later, no dependency) and commit the regenerated files with the data.
3. Open a pull request. The maintainer adds the version number and the CHANGELOG entry when merging. Checks validate the data, build the site and test the links.

**Selection:** the README lists only entries marked `featured = true`, the best of each group; the [full list](full-list.md) keeps every entry, inactive and dead ones included. See [MAINTENANCE.md](MAINTENANCE.md).

**What gets in:** resources useful to adult builders of official LEGO or compatible bricks, publicly reachable, active or still a reference. Shops must state their delivery terms; brands must have an official site. Each entry needs at least one source with a date.

**What stays out:** affiliate or referral links, link shorteners, pages that require an account to read, copies of copyrighted instructions, sellers of counterfeit sets presented as official LEGO, self-promotion without substance.

**Writing:** factual and short, no marketing words; decimal point, no thousands separator; prices including taxes; no abbreviations except proper names and technical terms.

By contributing, you agree that your contribution is published under the licenses of the repository (content: CC BY-NC-SA 4.0; code: PolyForm Noncommercial 1.0.0). Everyone follows the [code of conduct](CODE_OF_CONDUCT.md).
