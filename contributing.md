# Contributing

This list aims to be accurate and current, and complete where no reference exists. Every entry is checked at its source. Contributions are written in English. The website is bilingual: an entry proposed without French texts is accepted (the build warns « French translation missing »), shown in English on the French page, and the monthly review adds the French texts.

**Suggest without editing files:** open an issue with the [Add a resource](https://github.com/actarus314/awesome-lego/issues/new?template=add-resource.yml) or [Fix an entry](https://github.com/actarus314/awesome-lego/issues/new?template=fix-entry.yml) form. A maintainer writes the entry.

**Edit the data yourself:**
1. Edit the TOML file of the category in [`data/`](data/), following [`data/SCHEMA.md`](data/SCHEMA.md); a new entry gets `added` set to the day it enters the directory (it feeds the site's feed of new resources). `README.md`, `full-list.md` and the category list of the issue form are generated: do not edit them by hand.
2. Run `python3 scripts/build.py --check` (the latest Python release, no dependency; the checks run on it only) and commit the data only: `README.md`, `full-list.md`, the category list of the issue form, `VERSION` and `CHANGELOG.md` are written after the merge (a pull request that changes them fails its checks). To see the website, run `python3 scripts/build.py --site-only && python3 -m http.server -d site` and open http://localhost:8000. The checks of the pull request also run `python3 -m unittest discover -s tests` and, when the website changes, `python3 scripts/check_site.py` (needs `npm ci` and `pip install -r tests/requirements.txt`, then `python3 -m playwright install chromium`; add `--dejavu` to draw the page with the wider fonts of the GitHub runners).
3. Add a file `changes/<name>.md` (lowercase letters, digits and hyphens) that says what changes in two sentences, 550 characters at most, under its type: `major`, `minor` or `none`, as [MAINTENANCE.md](MAINTENANCE.md#versions) defines them (a major one adds a second line `series:`); a change of `data/` or the website without it fails the checks. For example

   ```
   type: minor

   Data: 3 museums in Denmark, and the address of a club that moved.
   ```

   The version number and the CHANGELOG entry are written from it after the merge. `python3 scripts/changes.py check` reads it.
4. Open a pull request. Checks validate the data, the fragment and the site; links are tested every week by a separate job.

**Code:** a change of the scripts, the workflows or the website comes with its tests in [`tests/`](tests/): a new function or check gets a test that fails without it (a check is tried on a defect planted on purpose), and a fixed bug gets a test that reproduces it. `python3 -m unittest discover -s tests` runs them; the Check workflow runs them on every pull request, and Render checks the website in a browser.

**Selection:** each entry may carry ranks 1 to 5 within its group, worldwide and per country or language (`rank`, with its reasons; see [`data/SCHEMA.md`](data/SCHEMA.md)); the README lists the rank 1 worldwide of each group, and "Where to start" on the website shows the entries ranked for the visitor's country or language. The [full list](full-list.md) keeps every entry, inactive and dead ones included. See [MAINTENANCE.md](MAINTENANCE.md).

**What is listed:** where a reference directory kept up to date already lists every resource of a kind (clubs of a country, channels of a language), the directory points to it and keeps the 3 to 5 that stand out per country or language in each group; unique places (museums, permanent exhibitions) and every active brand of compatible bricks that sells sets in Europe are listed in full. The [about page](https://3001.club/about/) says the same for visitors.

**What gets in:** resources useful to builders of every age (children, their parents and teachers, adults) of official LEGO or compatible bricks, in the 8 mm stud system, a smaller format or a construction system of its own ("Other formats"); resources only about large toddler blocks such as DUPLO stay out; publicly reachable, active or still a reference. Shops must state their delivery terms; brands must have an official site. Each entry needs at least one source with a date.

**What stays out:** affiliate or referral links, link shorteners, pages that require an account to read, copies of copyrighted instructions, sellers of counterfeit sets presented as official LEGO, self-promotion without substance.

**Links read at the source:** `brands` (alternative brands an entry sells, tracks, reviews or discusses), `funding` (how a comparator, review site or channel earns money), `makers` (who makes a brand's bricks) and `audience` (the public a resource states it is made for: children, adults, or both) are filled only from the resource's own pages or, for makers, from the brand, the maker or two independent sources; leave them out rather than guess. See [`data/SCHEMA.md`](data/SCHEMA.md).

**Writing:** factual and short, no marketing words; decimal point, no thousands separator; prices including taxes; no abbreviations except proper names, technical terms and the months of dates. The card's text says what sets the entry apart in 35 words at most; dates are written with the month in letters, abbreviated (3 Jul 2027); in French, « LEGO officiel » is a label only. Details: [`data/SCHEMA.md`](data/SCHEMA.md), "Writing rules"; the build refuses what does not follow them.

By contributing, you agree that your contribution is published under the licenses of the repository (content: CC BY-NC-SA 4.0; code: GNU AGPL 3.0). The licence of each file is set in [`REUSE.toml`](REUSE.toml) (texts in [`LICENSES/`](LICENSES/)) and checked by `reuse lint`: a new file outside the paths listed there needs its line. Brand logos (`media/logos/`) are trademarks of their owners, under none of these licences. Everyone follows the [code of conduct](CODE_OF_CONDUCT.md).
