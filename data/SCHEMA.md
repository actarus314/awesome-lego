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
covers = ["official", "alternative"]     # official | alternative | second-hand | parts | custom-builds | minifigures | instructions | news | data
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
confidence = "high"                      # high: read at the source | medium: indexed or third-party | low: single weak source
github = "owner/repo"                    # optional: for automatic stars and last-commit updates
youtube_channel_id = "UC…"               # optional: for automatic last-video updates (public RSS feed)
subreddit = "lepin"                      # optional: for automatic activity updates
feed = "https://…/feed"                  # optional: RSS or Atom feed of the resource

[[resource.sources]]                     # at least one; the page that supports the entry
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
