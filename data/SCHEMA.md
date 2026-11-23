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

[[resource]]
id = "brick-broker"                      # unique across all files, lowercase, hyphens
name = "Brick Broker"
url = "https://brick-broker.com/"        # canonical home page, https
group = "price-comparators"              # one of category.groups
featured = true                          # optional: listed in the README selection (best of its group)
aliases = ["Funwhole"]                   # optional, brands: other names the brand goes by, used to find mentions
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
status = "active"                        # active | slow (no update for 6 months) | inactive (12 months) | archived | dead
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

[[resource.sources]]                     # one to three, the strongest; a newer reading replaces the oldest source instead of adding a fourth
url = "https://brick-broker.com/a-propos"
date = "2026-11-23"                      # publication or update date of the source, else the reading date
kind = "official"                        # official | read (page read at the source) | indexed (search snippet, cache) | third-party | forum
```

Writing rules:
- Impersonal, factual, short. No marketing words. Facts not verified are left out or marked in `confidence`.
- Numbers: decimal point, no thousands separator (`42003`, `4.95 €`).
- English: "official LEGO" for the brand; French: « LEGO officiel ». Proper names keep their form (LEGO Ideas, LEGO.com).
- No abbreviations except proper names and technical terms (API, CSV, RSS). Write "custom builds" / « créations originales » rather than MOC.
- Prices including taxes.

## Other data files

- `data/journeys.toml`: the "Where to start" needs of the website (`[[journey]]` with `id`, `title_en`, `title_fr`, `scope`, `resources`, optional `always`). `resources` is one ranked list mixing international and local entries; the website keeps, in this order, the first 5 that suit the visitor: `scope = "country"` keeps international entries and those of the visitor's country (from the browser; for France, also entries with `ships_to_france`), `scope = "language"` keeps entries in the visitor's language or in English, `scope = "global"` keeps all; ids in `always` are kept for everyone. An unknown id or scope fails the build.
- `data/backend/`: figures used by the findings but not listed as entries, each file with its `source`, its reading `date` and its source `kind`. `clubs-by-country.json`: fan communities per country (ISO 3166-1 alpha-2) in the official LEGO Fan CoLab directory. `population.json`: World Bank population (SP.POP.TOTL) of the same countries.
- `data/metrics.json`: local cache of the last activity reading, written by `scripts/refresh.py`.
