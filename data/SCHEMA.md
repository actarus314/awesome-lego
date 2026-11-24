# Data schema

One TOML file per category in `data/`. Every text shown on the website exists in English (`_en`) and French (`_fr`); the README and the full list use English.

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
regime = "activity"                      # optional: activity | work | operating, the default of the entries of the group (see Regimes below)

[[resource]]
id = "brick-broker"                      # unique across all files, lowercase, hyphens
name = "Brick Broker"
url = "https://brick-broker.com/"        # canonical home page, https
group = "price-comparators"              # one of category.groups
featured = true                          # optional: listed in the README selection (best of its group)
aliases = ["Funwhole"]                   # optional, brands: other names the brand goes by, used by the search
covers = ["official", "alternative"]     # official | alternative | second-hand | parts | custom-builds | minifigures | instructions | news | data | events | places | clubs | learning
languages = ["fr", "en"]                 # ISO 639-1 codes of the interface or content
countries = ["FR"]                       # ISO 3166-1 alpha-2 codes served, or ["international"]
ships_to_france = true                   # shops only; omit when not relevant
access = "free"                          # free | free-account | freemium | paid
business_model_en = "Affiliate links"    # optional
business_model_fr = "Liens d'affiliation"
summary_en = "What it is and what it is for, one or two sentences."
summary_fr = "Ce que c'est et à quoi ça sert, une ou deux phrases."
strengths_en = ["Short factual point", "…"]
strengths_fr = ["Point factuel court", "…"]
weaknesses_en = ["…"]
weaknesses_fr = ["…"]
size_en = "42003 sets, 95 brands"        # optional, figures as published by the resource
size_fr = "42003 sets, 95 marques"
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
city = "Billund"                         # optional: places, events, clubs
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

Writing rules:
- Impersonal, factual, short. No marketing words. Facts not verified are left out or marked in `confidence`.
- Numbers: decimal point, no thousands separator (`42003`, `4.95 €`).
- English: "official LEGO" for the brand; French: « LEGO officiel ». Proper names keep their form (LEGO Ideas, LEGO.com).
- No abbreviations except proper names and technical terms (API, CSV, RSS). Write "custom builds" / « créations originales » rather than MOC.
- Prices including taxes.

## Other data files

- `brands`, `funding` and `makers` are read at the source and never deduced from the texts.
- `data/journeys.toml`: the "Where to start" needs of the website (`[[journey]]` with `id`, `title_en`, `title_fr`, `scope`, `resources`, optional `always`). `resources` is one ranked list mixing international and local entries; the website keeps, in this order, the first 5 that suit the visitor: `scope = "country"` keeps international entries and those of the visitor's country (from the browser; for France, also entries with `ships_to_france`), `scope = "language"` keeps entries in the visitor's language or in English, `scope = "global"` keeps all; ids in `always` are kept for everyone. An unknown id or scope fails the build.
- `data/backend/`: figures used by the website but not listed as entries, each file with its `source`, its reading `date` and its source `kind`. `clubs-by-country.json`: fan communities per country (ISO 3166-1 alpha-2) in the official LEGO Fan CoLab directory. `population.json`: World Bank population (SP.POP.TOTL) of the same countries. `geocode.json`: coordinates of each `city` (one point per city, `"City|CC"` keys, city precision, not addresses), from the public Nominatim service of OpenStreetMap (data © OpenStreetMap contributors, ODbL); written by `scripts/geocode.py`, which asks only for cities not yet in the file, at most one request per second.
- `data/metrics.json`: local cache of the last activity reading, written by `scripts/refresh.py`.
