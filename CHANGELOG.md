# Changelog

One short entry per version; the details are in its pull request and its commits.

# v4.x — The directory for builders of every age: children, their parents and teachers, as well as adults; an about page says how it is made and how to take part.

## v4.6 — 2026-11-27
Licence: the code is now under the GNU AGPL 3.0, a free software licence, instead of PolyForm Noncommercial; texts and data stay under CC BY-NC-SA 4.0, so they still exclude commercial reuse.

Automation: the scripts that read third-party pages, feeds and redirects are fuzzed every Thursday for 10 minutes (ClusterFuzzLite, fuzz/), and the five faults found by the first runs are fixed.

Automation: a pull request says what it changes in `changes/<name>.md`, and the Version workflow writes the number, the CHANGELOG entry and the generated files after the merge. Render installs its kept fonts without apt-get update.

Contributing: changes of code come with their tests, written down as a policy.

Tests: a check of the fragments no longer depends on the version of the repository.

## v4.5 — 2026-11-27
Website: on a slow phone the list shows sooner and the first touch of the search field no longer stalls the page, cards and search index being prepared while the browser is idle; events, clubs and courses say how often they recur; the chart of fan communities keeps its text size at 320 px. Also, without a number since v4.4: mechanical guards and the Tidy workflow (#31), a Renovate rule for the Python of Tidy (#32), release notes taken from this changelog (#33).

## v4.4 — 2026-11-26
Website: the about page keeps the place being read when the language changes, the share of active entries reads "still current" on one line, and the phone bar keeps to two lines with wider fonts too. Feed: named Awesome LEGO, without the event dates left from the calendar removed in v3.0.

## v4.3 — 2026-11-26
Website: search results grouped by category, each in the order of its best match; on a wide screen, a brand's strengths and weaknesses open with its banner and a filter panel used over the list stays open; phones: French bar on two lines, no zoom into the search field; page data 11 % lighter. Also: one short entry per version in this changelog.

## v4.2 — 2026-11-26
Website: the title of the about pages says how to take part, like their section (it still said how to write).

## v4.1 — 2026-11-26
Website: an about page in English and French (header tab, Settings menu on a phone, footer link) says what the directory is, how it is made, how the selection works and how to take part, with the licences and the LEGO trademark notice. Header and footer are shared by every page; contributing.md states the selection rule; MAINTENANCE.md is rewritten as a diagram and short tables.

## v4.0 — 2026-11-25
Data: a field `audience` gives the public an entry states it is made for (178 entries; an age printed on a box does not count), 29 resources for children and families join (749 in all), and builders of every age are admitted, toddler blocks such as DUPLO excepted. Website: filters and tags for children and adults, a "With children" tile, the visitor's country first, a Settings menu, a phone home page led by the search, a bar that folds on every screen, Back that restores the view, abbreviated months; the result count, empty since v3.4, is back.

# v3.x — The directory remodelled around what a visitor needs: "Where to start" by need, each brand on a banner of its own, cards whose every line is a structured field, and rules of writing checked by the build.

## v3.5 — 2026-11-25
Website: "Who makes the bricks" reads brand, maker, then dated sources in all three lists; a header button opens external links in a new tab (kept by the browser); a floating button goes back to the top; brand mode gets a larger logo, a way back to the whole directory and a LEGO banner that says why it lists only what the LEGO Group runs. Also: a preview of the website for each pull request (#19).

## v3.4 — 2026-11-25
Website: a "Suggest a resource" link right where a search ends — beside the count of the search bar (wide screens only, to keep the sticky bar on one line; kept in place but hidden when nothing matches), under the results, and in the "No resource matches" message — opens the "Add a resource" issue form; when nothing matches, the text searched becomes its title (100 characters at most); the footer keeps "Contribute" for the full guide.

## v3.2 — 2026-11-25
Data: 197 resources from an inventory of the brick world, each read at its source on 25 Nov 2026 (720 in all); 542 entries ranked 1 to 5 in their group, the rank 1 worldwide of each group (54) making the README selection, the ★ and the Selection filter; the 523 card texts rewritten to the v3.0 rules, every fact kept. Contributions are in English; removed: `featured`, `business_model_*`, `size_*`; corrections read at the source, among them the Discovery Centres bought by the LEGO Group on 27 Feb 2026.

## v3.1 — 2026-11-25
Automation: a link that fails from GitHub is opened again from 3 Globalping probes on home and office networks; the links issue lists as broken only what fails everywhere twice, adds dead pages (parked domain, closure notice) and opens only when a person is needed. The weekly data report becomes monthly, the day before the monthly review; Data fixes runs after Links; MAINTENANCE.md lists the owner's tasks.

## v3.0 — 2026-11-24
Removed: the "Out and about" view (map, calendar `agenda.ics`, near me, Nominatim) and the business-model texts. Website: "Where to start" in 10 needs, brand mode on a banner with its logo (27 brands), cards with plain statuses, access labels and the other entries of the same site, strengths and weaknesses read after the page (17 % sooner on a slow phone). Data: `rank_scope`, `rank`, `operator`, structured `size`, local city names, rules of writing checked by the build; REUSE licences; site source split into four files.

# v2.x — The directory read at the source down to its links: which brands each entry deals with, how it is funded, who makes the bricks; a website in three views, directory, out and about, observatory.

## v2.17 — 2026-11-24
Website: the group of a card is back beside the entry's name, on one line, in a short form (`short_en`, `short_fr` of a group, 17 characters at most, required by the build when the name is longer); a long entry name wraps under it instead. The rendering check fails on a group label that is not on the first line, beside the name.

## v2.16 — 2026-11-24
Data: groups merged where a visitor looking in one would want the other (54 groups instead of 60: Mattel and Revell with the European brands, chat servers with the forums, touring exhibitions with the conventions…). Website: a card's group stands above its name, checked by the rendering check.

## v2.15 — 2026-11-24
Checks: the accessibility rules of the rendering check are a guard, not a conformance target; the 13 px studs of the category map are accepted by name, so that a newer version of axe-core cannot fail the check on them; the page is scrolled back to the top before the rules run, as a sticky header over a scrolled view made two heat map cells of the observatory look covered.

## v2.14 — 2026-11-24
Data: each entry has a regime that says what keeps it current: activity (sites, channels, forums, software: status from the last post), work (books, guides, standards: never inactive by age) or operating (places, shops, brands, clubs: open or closed, checked by the review). 17 entries no longer show as slow or inactive.

## v2.13 — 2026-11-24
Automation: the Data fixes pull request can be opened with the token of a GitHub App or a personal token, so that its checks start on their own instead of waiting for an approval.

## v2.12 — 2026-11-24
Automation: everything follows its latest release. Renovate proposes an update 3 days after it is published (at once for a security fix, as Dependabot does), and now also follows MiniSearch and the fonts of the Brick Vault, whose files the website keeps: `scripts/vendor.py` copies them from the locked packages and Check fails when they differ. The checks run on the latest Python release only (the job on Python 3.11 is removed).

## v2.11 — 2026-11-24
Checks: the links issue lists first the links that failed twice in a row, then those that failed once (from the machines of GitHub, many sites time out or refuse the connection for a day and answer again the next week), with a reminder to open a link in a browser before changing its entry.

## v2.10 — 2026-11-24
Data: the Palais de la Maquette linked by http (self-signed certificate). Checks: security-policy hashes computed with an HTML parser (two code scanning alerts), rendering check on Node 26 and Python 3.15; the links check counts 401 and 405 as answers, skips local addresses and retries three times.

## v2.9 — 2026-11-24
Website: with the wider fonts of some systems (DejaVu Sans, as on Linux and on the GitHub runners), entry names on narrow phones and brand names of the observatory's heat map no longer break inside a word: an entry's category moves below its name, and the heat map scrolls inside its own box. Checks: the rendering check can draw the page with those fonts (`--dejavu`), the way the Render workflow sees it.

## v2.8 — 2026-11-24
Checks: a rendering check (workflow Render) opens every view in a real browser, both languages, five widths, and fails on overflows, split labels, cut words, script errors and WCAG 2.2 A or AA violations found by axe-core. Website: focus, keyboard, contrast and 24 px targets fixed; on a slowed phone, layout shift 0.93 → 0, list painted 2.0 → 1.5 s, blocking time 0.96 → 0.38 s.

## v2.7 — 2026-11-24
Website: a few hints towards the Brick Vault, for those who look. A faint line of arrows in the footer, a comment in the page source, a message in the browser console, a search suggestion for words such as "secret", "cheat" or "konami" (five letters at least, so it never crowds an ordinary search), and the logo that hops while the code is being typed.

## v2.6 — 2026-11-24
Website: in the calendar and the list near the map, the website and "On the map" join the contact lines, in the same form (icon, then the site's name or the action), instead of a separate row of links; the contact lines of the calendar no longer inherit the frame of the calendar rows.

## v2.5 — 2026-11-24
Website: contact details take one line each (address, phone, email), with an icon; a phone number, an email, a town or a postal code no longer breaks across two lines, and two addresses no longer run into each other. On phones and tablets, the list near the map grows with its content instead of scrolling inside the page, as intended since v2.1.

## v2.4 — 2026-11-24
Website: an easter egg. The Konami code (↑ ↑ ↓ ↓ ← → ← → B A, or on a touch screen four swipes up, down, left and right in that order, then two taps) opens the Brick Vault (`vault/`, English only): a baseplate where bricks drop and stack, five cheat codes to find and nine achievements, kept in the browser. Its two fonts (Press Start 2P and Nunito, SIL Open Font License) are served by the site itself; the page contacts nothing else and is not indexed.

## v2.3 — 2026-11-24
Website: an address opens Google Maps, which phones hand to their maps app, instead of OpenStreetMap; showing a city of the list on the map no longer scrolls that city to the top of the list.

## v2.2 — 2026-11-24
Data: a `contact` field gives the address, phone and email that 60 places, events and clubs publish as their own (never a private person's), shown on their cards. Removed: the "Independent" criterion (7 entries out of 523). Automation: a publication after a push reuses the day's measurements (about one minute instead of four).

## v2.1 — 2026-11-24
Website, out and about: the map comes first, then the calendar, whose entries unfold in place; the map zooms and shows several kinds as slices; a typed city sets the starting point (Nominatim, only when submitted); the calendar becomes a `webcal:` subscription. Removed: subtitles and sentences that repeated the screen.

## v2.0 — 2026-11-24
Data: three fields read on the entries' own pages, `brands` (107 entries), `funding` (109) and `makers` (17 brands, kept only when the brand or maker states it or two independent sites confirm it). Website in three views, Directory, Out and about (calendar, map drawn by the site) and Observatory (the former Findings), under a content security policy that allows only the site's own scripts.

# v1.x — Bilingual directory of the brick world, from brands and shops to events, places, clubs and know-how: resources checked at their source, best-of README, website with map, journeys and findings, automatic updates.

## v1.18 — 2026-11-23
Website: "Where to start" adapts to the visitor. Each need keeps one ranked list mixing international and local entries, and the page shows the first five that suit the visitor's country (buying, second-hand, visiting, meeting fans) or language (news, reviews, learning), from the browser.

## v1.17 — 2026-11-23
Website: "In French" gives way to one button per language, combinable: the visitor's browser language, the page language and English (for example "In German" and "In English"), kept in the address as `lang=`.

## v1.16 — 2026-11-23
Website: within each group, entries in the visitor's browser language come first, then English, then the others; nothing is hidden. Real icon files (PNG, ICO, Apple touch icon) replace the inline one, and the feeds carry their icon, so feed readers show it.

## v1.15 — 2026-11-23
23 national references added where fans are many and the directory was thin: conventions, clubs, news sites and price comparators of the United States, Canada, Australia, New Zealand, South Africa and Italy; 522 resources in all.

## v1.14 — 2026-11-23
Website: the dates of the data (last check at the source, last activity reading) move to the top of the page, sources are shown by site name, and an entry reached by a link stays below the filter bar. Data: at most three sources per entry; the "Blind spots" finding leaves the website for the weekly report, where it lists the countries to cover.

## v1.13 — 2026-11-23
The website's feed now follows the content, in each language: new resources and announced event editions (`feed.xml`, `fr/feed.xml`); the feed of versions moves to `changes.xml`. Each entry carries the date it entered the directory (`added`), and the feed is linked from the footer and the README.

## v1.12 — 2026-11-23
Website: the English home page sends a browser set to French to the French page, until a language is chosen with the language button; the theme already follows the browser until one is chosen.

## v1.11 — 2026-11-23
Findings laid out in balanced columns, the oldest silent resources of a category grouped in one counted ring, and the map's subtitle removed. Every build now checks that MAINTENANCE.md and data/SCHEMA.md still name each workflow, schedule, controlled word and backend file, and regenerates the category list of the "Add a resource" form, which still listed the 8 first categories.

## v1.10 — 2026-11-23
97 resources added where the directory was thin (storage, display, trains, Technic and programming, minifigures, Italy, Spain, Poland, Benelux, the Nordics, thirteen subreddits): 499 in all. Automation: subreddits through the Arctic Shift archive, 62 site feeds, daily measurements on a history branch, a weekly Data fixes pull request; Atom feed of versions.

## v1.9 — 2026-11-23
Website: the Directory tab leads to the map, the count of each category sits in its own badge, and on phones the filters fold behind a "Filters" button that shows how many are on.

## v1.8 — 2026-11-23
README: each category icon sits on its heading line and categories are spaced apart. Website: the date after "checked" now reads "last activity".

## v1.7 — 2026-11-23
Website: category icons come back in the headings of the directory list, not on the map tiles.

## v1.6 — 2026-11-23
Website: the day theme becomes "Bleu jour", the daylight counterpart of the night palette (pale blue grid, navy text, blue interface); category icons stay in the README only.

## v1.5 — 2026-11-23
README and website: one icon per category, shorter category names and texts, softer day colours (brick red for official LEGO, amber for alternative brands), one colour per filter family, the alternative-brand chart in the interface teal, and the entry reached from a stud, a journey or a dot stays highlighted. README selection reviewed: 91 entries (nanoblock, eBay, BrickPlus, Brick Me Up Scottie, Frostiize and the LEGO Builder app out; the LEGO Store directory in).

## v1.4 — 2026-11-23
Four new categories checked at their source: events (42), places (38), clubs (30) and learning (44), 402 resources in all and 96 in the README; three journeys follow them (visit, meet, understand), event cards show their next edition and a country filter joins the criteria. New finding "Where the passion is": fan communities recognized by LEGO (Fan CoLab, 178 in 45 countries) against World Bank population, by country.

## v1.3 — 2026-11-23
Website: "Where to start" with six needs and their best resources, card or sortable table view, several categories at once, filter families renamed Scope and Criteria, search and filters kept in the address, day colours that tell official LEGO (red) from alternative brands (blue), title level with the figures, link preview image. README: one short description per entry and a logo.

## v1.2 — 2026-11-23
Website: findings move to their own view (Directory and Findings tabs, address #findings); the French-availability chart is removed; the pulse shows each resource silent for 6 months as a clickable ring and counts the active ones. Each page now carries its own language only (page weight down by about 30 %) and the search waits for a pause in typing.

## v1.1 — 2026-11-23
Website: ranked, typo-tolerant search (MiniSearch, also over weaknesses, countries and brand names), filters in three labelled families, a stud of the map opens its entry, the "Bleu" night palette for the dark theme. The six charts give way to three findings: which listed resources talk about each alternative brand, how much exists in French for alternative brands against official LEGO, and the pulse of last activity.

## v1.0 — 2026-11-23
First public version: 248 resources in 8 categories, each checked at its source, 76 selected for the README, full list, bilingual website with map, six charts, search and filters. Community files, security settings, daily site rebuild with fresh activity data, weekly data report and link check.
