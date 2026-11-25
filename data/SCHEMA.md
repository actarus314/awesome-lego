# Data schema

One TOML file per category in `data/`. Every text shown on the website exists in English (`_en`) and French (`_fr`); the README and the full list use English. A proposed entry may come in English only: without `summary_fr`, it carries no French text at all, the build warns « French translation missing », the French page shows the English texts marked as English, and the monthly review adds the French texts.

```toml
[category]
id = "comparators"                       # file name without .toml
name_en = "Price comparators and set databases"
name_fr = "Comparateurs de prix et bases de sets"
summary_en = "One sentence."
summary_fr = "Une phrase."

[[category.groups]]                      # subcategories, in display order
id = "price-comparators"
name_en = "Price comparators"
name_fr = "Comparateurs de prix"
short_en = "Price comparison"            # optional: label on the cards, 17 characters at most (needed when the name is longer)
short_fr = "Comparateurs"
regime = "activity"                      # optional: activity | work | operating, the default of the entries of the group (see Regimes below)
rank_scope = "country"                   # country | language | intl: the entries of the group are ranked per country, per language, or once worldwide

[[resource]]
id = "brick-broker"                      # unique across all files, lowercase, hyphens
name = "Brick Broker"
url = "https://brick-broker.com/"        # canonical home page, https
group = "price-comparators"              # one of category.groups
rank = {intl = 1, FR = 2}                # optional: rank 1 to 5 of the entry in its group, worldwide (intl) and per country or language (codes of the group's rank_scope); one entry per rank, group and scope; none on a dead, archived or inactive entry. The rank 1 intl of each group is the selection (README, ★, filter)
rank_reason_en = "Largest comparator of French shops, prices read every day"   # with rank: why (not shown)
rank_reason_fr = "Plus grand comparateur des boutiques françaises, prix relevés chaque jour"
operator = "lego-group"                  # optional: lego-group | licensee, sites and places run by the LEGO Group itself, or under the LEGO brand by a partner (LEGO Certified Stores, LEGOLAND parks)
audience = ["children"]                  # optional: the publics the resource states it is made for or has a specific offer for, read on its own pages: children (children, young people or families: an age range ending at 17 or below, a junior section, workshops, a school programme, sets marketed to children) | adults (adult fans, or membership or entry from 16 or 18); both when both are stated; absent when no particular public is stated (a shop, a database, a museum for everyone)
aliases = ["Funwhole"]                   # optional, brands: other names the brand goes by, used by the search
covers = ["official", "alternative"]     # official | alternative | second-hand | parts | custom-builds | minifigures | instructions | news | data | events | places | clubs | learning
languages = ["fr", "en"]                 # ISO 639-1 codes of the interface or content
countries = ["FR"]                       # ISO 3166-1 alpha-2 codes served, or ["international"]
ships_to_france = true                   # shops only; omit when not relevant
access = "free"                          # free | free-account | freemium | paid, with a meaning that depends on the category (see Access below)
summary_en = "What is particular about it, one or two sentences, 35 words at most."   # see Writing rules: the card already shows the name, the group, the country and the tags
summary_fr = "Ce qu'elle a de particulier, une ou deux phrases, 35 mots au plus."
strengths_en = ["Short factual point", "…"]
strengths_fr = ["Point factuel court", "…"]
weaknesses_en = ["…"]
weaknesses_fr = ["…"]
size = [{n = 42003, unit = "sets"}, {n = 95, unit = "brands"}]   # optional, figures as published by the resource; approx = "about" | "more-than" | "at-least" when published so; unit: see Sizes below
status = "active"                        # active | slow (no update for 6 months) | inactive (12 months) | archived | dead; slow and inactive for the regime activity only
regime = "work"                          # optional, also on category.groups (default for the group, else activity): activity | work | operating
last_activity = "2026-11-23"             # ISO date of the last observed activity (post, video, commit, price update)
checked = "2026-11-23"                   # ISO date of the last verification of this entry
added = "2026-11-23"                     # ISO date the entry entered the directory, set once and never changed (content feed)
confidence = "high"                      # high: read at the source | medium: indexed or third-party | low: single weak source
github = "owner/repo"                    # optional: for automatic stars and last-commit updates
youtube_channel_id = "UC…"               # optional: for automatic last-video updates (public RSS feed)
subreddit = "lepin"                      # optional: for automatic activity updates
feed = "https://…/feed"                  # optional: RSS or Atom feed of the resource
city = "Billund"                         # optional: places, events, clubs; one city, its usual English name (Vienna, Antwerp)
city_fr = "Vienne"                       # optional: the usual French name, only when it differs from city
city_local = "Wien"                      # optional: the local name, only when it differs from city (found by the search)
next_date = "2027-06-12"                 # optional, events: start of the next edition (ISO date)
recurrence_en = "Every June"             # optional, events: how often it happens
recurrence_fr = "Chaque juin"
brands = ["cobi", "cada"]                # optional, not in brands.toml: ids of the alternative brands of brands.toml that the resource sells, tracks, reviews or admits, as read on its own pages; [] when read and none; absent when not read
funding = ["affiliation", "ads"]         # optional, comparators, reviews, videos: affiliation | ads | sponsorship | subscription | donations | shop | none | unknown (none and unknown alone), as read at the source

[[resource.sources]]                     # one to three, the strongest; a newer reading replaces the oldest source instead of adding a fourth
url = "https://brick-broker.com/a-propos"
date = "2026-11-23"                      # publication or update date of the source, else the reading date
kind = "official"                        # official | read (page read at the source) | indexed (search snippet, cache) | third-party | forum

[resource.contact]                       # optional, places, events, clubs: the public contact the entity publishes as its own, read on its official site; url, date and at least one of address, phone, email
address = "…, 7190 Billund"             # the place (several places: separated by " ; "); for an event, the venue of the next edition; for a club, a public meeting place only, never a member's home
phone = "+45 …"                         # international format; businesses, venues and organisers only, never a private person's number
email = "info@…"                        # the address published as the entity's contact; none when only a form exists
url = "https://…/contact"                # page where they were read
date = "2026-11-24"

[[resource.makers]]                      # optional, brands.toml only: who makes the bricks, one table per maker, each with its own source
name = "GoBricks"                        # the company, or a short description when it is not named
name_fr = "…"                            # required when the maker has no id (a description, shown in French)
id = "gobricks"                          # optional: the maker's id when it is an entry of brands.toml (the brand's own id when it makes its own bricks)
url = "https://pantasy.com/pages/about-us"
date = "2026-11-23"
kind = "official"                        # official | read | third-party; a maker resting on third-party sources needs two independent sites, unless the brand or the maker states it (a forum or a search snippet is never enough)
```

Regimes (`regime`, on a group or an entry): what keeps an entry current, and so how its status is read.
- `activity` (default): a site, a channel, a forum, software. The status follows `last_activity`: active up to 6 months, slow up to 12, inactive beyond; a recurring event with an announced `next_date` stays active.
- `work`: a finished work whose value does not depend on new posts (book, article, guide, glossary, standard, ruling, patent). `last_activity` is the date of its latest edition or revision, shown as such; the status is active, or archived once a review finds it outdated, or dead when it is gone.
- `operating`: an entity that is open or closed (place, shop, marketplace, brand, club, programme). Its posts do not measure it; the review checks that it still operates (`checked`); the status is active, archived or dead.

Access (`access`): what the value describes depends on the category, and a value outside its category fails the build. Labels: `site-src/strings.json`, keys `acc_<context>_<value>`.
- `entry` (places, events): free | paid entry.
- `membership` (clubs): free | paid membership (a fee).
- `competition` (events, group competitions): free | free-account (an account is required to enter).
- `use` (tools, comparators, learning): free | freemium (paid options) | paid | free-account (an account is required).
- `open` (community, video, directories, events of the group calendars): nothing when free to read; free-account (an account is required) | freemium (paid options).
- brands, shops, second-hand: no `access` (what they sell says it).

Sizes (`size`, unit): sets | brands | members | topics | posts | subscribers | videos | episodes | entries | associations | square-metres | bricks | parks | minifigures | parts | products | shops | ads | visitors | exhibitors | models | articles | countries | events | clubs | communities | instructions | reviews | followers | editions. A new unit is added to `UNITS` of `scripts/build.py` and to `site-src/strings.json`.

Writing rules:
- Impersonal, factual, short. No marketing words. Facts not verified are left out or marked in `confidence`.
- Numbers: decimal point, no thousands separator (`42003`, `4.95 €`).
- The brand. English: "official LEGO". French: « LEGO officiel » is a label only (a filter, a legend, a heading against « marques alternatives »); in a sentence, « de marque LEGO » for a product (sets, parts, minifigures, prices), « du groupe LEGO » for what the company runs (shop, stores, centres), « sous enseigne LEGO » for a store or a place run by a partner (LEGO Certified Stores, LEGOLAND parks). Proper names keep their form (LEGO Ideas, LEGO.com).
- Dates in texts: the month in letters, never abbreviated (3 July 2027, 3 juillet 2027, 1er avril), never 2027-07-03 nor 03/07/2027. Data fields (`checked`, `next_date`…) stay ISO dates; the website writes them in letters.
- The card's text (`summary_*`): what sets the entry apart, in one or two sentences of 35 words at most; it does not repeat the name, the group, the country or the tags, and starts with what distinguishes the entry. Everything else of the card's legend comes from structured fields (`city`, `size`, `next_date`, `funding`).
- No abbreviations except proper names and technical terms (API, CSV, RSS). Write "custom builds" / « créations originales » rather than MOC.
- Prices including taxes.

## Other data files

- `brands`, `funding`, `makers` and `audience` are read at the source and never deduced from the texts.
- `data/journeys.toml`: the needs of "Where to start" (`[[need]]`), in display order: `id`, `title_en`, `title_fr`; `category` (the icon of the tile and its last link, the whole category); `groups` (`<category>/<group>`, where the entries of the tile come from); `scope` (`country`, `language` or `intl`: how the visitor is matched, from the browser); optional `mode = "brand"` (entries open the brand mode of the search); optional `audience = "children"` or `"adults"` (only the entries of that public; the tile ends on its filter instead of the category); optional `reference = {FR = "<id>", default = "<id>"}` (the reference of the visitor's country or language first: national calendar, directory of associations, comparator; else `default`). The entries of a tile are those of its groups ranked for the visitor (`rank` in the visitor's country or language, then `intl`). An unknown id, group, category, scope or key fails the build.
- `data/backend/`: figures used by the website but not listed as entries, each file with its `source`, its reading `date` and its source `kind`. `clubs-by-country.json`: fan communities per country (ISO 3166-1 alpha-2) in the official LEGO Fan CoLab directory. `population.json`: World Bank population (SP.POP.TOTL) of the same countries.
- `data/metrics.json`: local cache of the last activity reading, written by `scripts/refresh.py`.
