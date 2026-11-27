#!/usr/bin/env python3
"""Validate data/*.toml, write README.md (the rank 1 worldwide of each group) and full-list.md
(every entry), and build the bilingual GitHub Pages site (site/).

Usage: python3 scripts/build.py [--check [--strict | --pull-request] | --site-only]   (standard library only, latest Python release)
--check: generated files out of date warn while a fragment of changes/ waits, fail otherwise; --pull-request (Check on
a pull request): always a warning; --strict (the pull request of the workflow Version): always an error.
"""
import base64
import datetime as dt
import hashlib
import html
import html.parser
import json
import pathlib
import re
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITE = ROOT / "site"
REPO = "actarus314/awesome-lego"
PAGES = "https://actarus314.github.io/awesome-lego/"
LANGS = ("en", "fr")
ORDER = ["brands", "shops", "comparators", "second-hand", "community", "video", "events", "places", "clubs", "learning", "tools", "directories"]
COVERS = {"official", "alternative", "second-hand", "parts", "custom-builds", "minifigures", "instructions", "news", "data", "events", "places", "clubs", "learning"}
ACCESS = {"free", "free-account", "freemium", "paid"}
# what `access` describes depends on the category (decision of 24/11/2026, 12:18): the entry of a place or an event,
# the membership of a club, entering a competition, using a tool; nothing for brands, shops and second-hand, nothing
# when free for news, communities, videos and directories. Label of each pair: strings.json, "acc_<context>_<value>".
ACCESS_CONTEXT = {"places": "entry", "events": "entry", "clubs": "membership", "tools": "use", "comparators": "use", "learning": "use",
                  "community": "open", "video": "open", "directories": "open"}
ACCESS_GROUP = {("events", "competitions"): "competition", ("events", "calendars"): "open"}  # websites, not events one enters
ACCESS_BY = {"entry": {"free", "paid"}, "membership": {"free", "paid"}, "competition": {"free", "free-account"},
             "use": {"free", "freemium", "paid", "free-account"}, "open": {"free-account", "freemium"}}
AUDIENCES = ("children", "adults")  # the publics an entry states it is made for or has a specific offer for; absent: no particular public
OPERATORS = {"lego-group", "licensee"}  # sites and places of the LEGO Group itself, or under the LEGO brand by a partner
RANK_SCOPES = {"country", "language", "intl"}  # a group ranks its entries per country, per language, or once worldwide
RANK = range(1, 6)
UNITS = {"sets", "brands", "members", "topics", "posts", "subscribers", "videos", "episodes", "entries", "associations",
         "square-metres", "bricks", "parks", "minifigures", "parts", "products", "shops", "ads", "visitors", "exhibitors",
         "models", "articles", "countries", "events", "clubs", "communities", "instructions", "reviews", "followers", "editions"}
APPROX = {"about", "more-than", "at-least"}
STATUS = {"active", "slow", "inactive", "archived", "dead"}
CARD_LABEL = 17  # characters of a group label on a card, beside the entry's name, on one line down to 320 px
REGIMES = {"activity", "work", "operating"}  # what keeps an entry current: recent activity, nothing (a finished work), being open
CONFIDENCE = {"high", "medium", "low"}
KINDS = {"official", "read", "indexed", "third-party", "forum"}
FUNDING = {"affiliation", "ads", "sponsorship", "subscription", "donations", "shop", "none", "unknown"}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ID = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

T = {  # interface strings
    "title": {"en": "Awesome LEGO", "fr": "Awesome LEGO"},
    "tagline": {"en": "Interlocking plastic construction bricks, from the official LEGO system to compatible brands.",
                "fr": "Briques de construction en plastique à emboîter, du système LEGO aux marques compatibles."},
    "site_tagline": {"en": "The best of the brick world for building at any age, in official LEGO and compatible brands.",
                     "fr": "Le meilleur du monde de la brique pour construire à tout âge, en sets de marque LEGO comme en marques compatibles."},
    "feed": {"en": "Feed of new resources (RSS)", "fr": "Flux des nouveautés (RSS)"},
    "contents": {"en": "Contents", "fr": "Sommaire"},
    "contributing": {"en": "Contributing", "fr": "Contribuer"},
    "contrib_text": {"en": "Additions and corrections are welcome: read [how the directory is made and what gets in](https://actarus314.github.io/awesome-lego/about/), then [contributing.md](contributing.md). Entries live in [`data/`](data/); this file is generated from them."},
    "site_fr": {"en": "French version of the website", "fr": "Version française du site"},
    "site": {"en": "Explore the website: every resource, with search, filters and a map", "fr": "Explorer le site : toutes les ressources, avec recherche, filtres et carte"},
}


def fail(errors):
    for e in errors:
        print("✗", e, file=sys.stderr)
    sys.exit(1)


def load():
    cats, errors, ids, urls = [], [], {}, {}
    notes.clear()
    untranslated.clear()
    for path in sorted(DATA.glob("*.toml")):
        if path.stem in ("metrics", "journeys"):
            continue
        try:
            d = tomllib.loads(pathlib.Path(path).read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as exc:
            errors.append(f"{path.name}: {exc}")
            continue
        c = d.get("category", {})
        where = path.name
        if c.get("id") != path.stem:
            errors.append(f"{where}: category.id must be '{path.stem}'")
        for k in ("name_en", "name_fr"):
            if not c.get(k):
                errors.append(f"{where}: category.{k} missing")
        groups = [g["id"] for g in c.get("groups", [])]
        for g in c.get("groups", []):
            for lang in LANGS:  # the label of a card stands on one line beside the entry's name
                if len(g.get("short_" + lang) or g.get("name_" + lang, "")) > CARD_LABEL:
                    errors.append(f"{where}: group {g['id']}: short_{lang} needed, the card label holds {CARD_LABEL} characters at most")
            if g.get("regime", "activity") not in REGIMES:
                errors.append(f"{where}: group {g['id']}: regime must be one of {sorted(REGIMES)}")
            if g.get("rank_scope") not in RANK_SCOPES:
                errors.append(f"{where}: group {g['id']}: rank_scope must be one of {sorted(RANK_SCOPES)}")
        scope = {g["id"]: g.get("rank_scope") for g in c.get("groups", [])}
        for r in d.get("resource", []):
            w = f"{where}: {r.get('id', '?')}"
            if not ID.match(r.get("id", "")):
                errors.append(f"{w}: bad id")
            elif r["id"] in ids:
                errors.append(f"{w}: id already used in {ids[r['id']]}")
            ids[r.get("id")] = where
            for k in ("name", "url", "group", "summary_en", "status", "checked", "added", "confidence"):
                if not r.get(k):
                    errors.append(f"{w}: {k} missing")
            if "featured" in r:  # replaced by the ranks in lot 3b
                errors.append(f"{w}: featured is replaced by rank (the rank 1 worldwide of a group is its selection)")
            if not r.get("summary_fr"):  # contributions in English only (decision of 24/11/2026, 13:47): the monthly review translates
                frk = [k for k in r if k.endswith("_fr") and k not in ("city_fr", "rank_reason_fr")]
                if frk:
                    errors.append(f"{w}: French texts come together, with summary_fr ({', '.join(frk)} without it)")
                untranslated.append(w)
            if len(r.get("sources", [])) > 3:  # the best three; a newer reading replaces the oldest instead of piling up
                errors.append(f"{w}: more than 3 sources")
            if not re.match(r"https?://", str(r.get("url", ""))):
                errors.append(f"{w}: url must start with https:// or http://")
            u = re.sub(r"^https?://(www\.)?", "", str(r.get("url", "")).rstrip("/").lower())
            # A brand and its own shop may share a URL; nothing else may.
            if u in urls and {urls[u][1], path.stem} != {"brands", "shops"}:
                errors.append(f"{w}: url already used by {urls[u][0]}")
            urls[u] = (r.get("id"), path.stem)
            if r.get("group") not in groups:
                errors.append(f"{w}: group '{r.get('group')}' not in category.groups")
            r["_regime"] = regime(r, c)
            if r["_regime"] not in REGIMES:
                errors.append(f"{w}: regime must be one of {sorted(REGIMES)}")
            elif r["_regime"] != "activity" and r.get("status") in ("slow", "inactive"):
                errors.append(f"{w}: status '{r['status']}' measures activity; an entry of regime {r['_regime']} is active, archived or dead")
            if set(r.get("covers", [])) - COVERS:
                errors.append(f"{w}: unknown covers {set(r['covers']) - COVERS}")
            if r.get("access") and r["access"] not in ACCESS:
                errors.append(f"{w}: unknown access '{r['access']}'")
            elif r.get("access") and r["access"] not in ACCESS_BY.get(access_context(path.stem, r.get("group")), set()):
                notes.append(f"{w}: access '{r['access']}' says nothing for {access_context(path.stem, r.get('group')) or 'this category'} (allowed: {sorted(ACCESS_BY.get(access_context(path.stem, r.get('group')), set())) or 'none'})")
            if "," in str(r.get("city", "")):
                notes.append(f"{w}: city holds one city (the main one; the others in the text)")
            if r.get("city_fr") is not None and (not r["city_fr"] or r["city_fr"] == r.get("city") or not r.get("city")):
                errors.append(f"{w}: city_fr only when the French name differs from city")
            if r.get("city_local") is not None and (not r["city_local"] or r["city_local"] == r.get("city") or not r.get("city")):
                errors.append(f"{w}: city_local only when the local name differs from city")
            au = r.get("audience")
            if au is not None and (not isinstance(au, list) or not au or set(au) - set(AUDIENCES) or len(set(au)) != len(au)):
                errors.append(f"{w}: audience is a list of {list(AUDIENCES)} (absent when no particular public is stated)")
            if r.get("operator") is not None and r["operator"] not in OPERATORS:
                errors.append(f"{w}: operator must be one of {sorted(OPERATORS)}")
            rk = r.get("rank")
            if rk is not None:
                sc = scope.get(r.get("group"))
                code = {"country": r"[A-Z]{2}", "language": r"[a-z]{2}", "intl": r"(?!)"}.get(sc, r"(?!)")
                if not isinstance(rk, dict) or not rk or any(not (k == "intl" or re.fullmatch(code, k)) or v not in RANK or isinstance(v, bool) for k, v in rk.items()):
                    errors.append(f"{w}: rank is a table {{intl = 1, <{'code' if sc == 'intl' else sc} code> = 2}} of ranks 1 to 5 (group scope: {sc})")
                elif r.get("status") in ("dead", "archived", "inactive"):  # a rank sends visitors to the entry (Where to start, README)
                    notes.append(f"{w}: rank on an entry whose status is {r['status']}")
                elif not (r.get("rank_reason_en") and r.get("rank_reason_fr")):
                    notes.append(f"{w}: rank_reason_en and rank_reason_fr say why the entry has its rank")
            sz = r.get("size")
            if sz is not None and (not isinstance(sz, list) or not sz or any(not isinstance(x, dict) or set(x) - {"n", "unit", "approx"} or not isinstance(x.get("n"), (int, float))
                                                                                or isinstance(x.get("n"), bool) or x.get("unit") not in UNITS or x.get("approx", "about") not in APPROX for x in sz)):
                errors.append(f"{w}: size is a list of {{n = 42003, unit = \"sets\"}} (unit in {sorted(UNITS)}, approx in {sorted(APPROX)})")
            if r.get("size_en"):
                notes.append(f"{w}: size_en and size_fr are free text: write size = [{{n = …, unit = …}}]")
            if r.get("business_model_en"):
                notes.append(f"{w}: business_model_en and business_model_fr are not shown: write funding (read at the source) or drop them")
            if r.get("status") not in STATUS:
                errors.append(f"{w}: unknown status '{r.get('status')}'")
            if r.get("confidence") not in CONFIDENCE:
                errors.append(f"{w}: unknown confidence '{r.get('confidence')}'")
            for k in ("checked", "last_activity"):
                if r.get(k) and not DATE.match(str(r[k])):
                    errors.append(f"{w}: {k} must be YYYY-MM-DD")
            for a, b in (("strengths_en", "strengths_fr"), ("weaknesses_en", "weaknesses_fr")):
                if r.get("summary_fr") and len(r.get(a, [])) != len(r.get(b, [])):
                    errors.append(f"{w}: {a} and {b} differ in length")
            for a in ("size", "business_model"):
                if bool(r.get(a + "_en")) != bool(r.get(a + "_fr")):
                    errors.append(f"{w}: {a}_en and {a}_fr must both be set")
            if not r.get("sources"):
                errors.append(f"{w}: at least one source required")
            for s in r.get("sources", []):
                if not str(s.get("url", "")).startswith("http") or s.get("kind") not in KINDS or not DATE.match(str(s.get("date", ""))):
                    errors.append(f"{w}: source needs url, date YYYY-MM-DD and kind in {sorted(KINDS)}")
            for k, v in r.items():
                if isinstance(v, str) and re.search(r"\d[  ]\d{3}\b", v):
                    errors.append(f"{w}: {k}: thousands separator in a number")
            f = r.get("funding")
            if f is not None and (not f or set(f) - FUNDING or len(set(f)) != len(f) or (("unknown" in f or "none" in f) and len(f) > 1)):
                errors.append(f"{w}: funding must list words of {sorted(FUNDING)}, each once, with unknown or none alone")
            for k, pat in (("url", r"https?://\S+"), ("feed", r"https?://\S+"), ("github", r"[\w.-]+/[\w.-]+"), ("youtube_channel_id", r"UC[\w-]{22}"), ("subreddit", r"\w{2,21}")):
                if r.get(k) is not None and not re.fullmatch(pat, str(r[k])):
                    errors.append(f"{w}: {k} malformed (expected {pat})")  # these values end up in addresses read by the scripts
            for s_ in r.get("sources", []) + r.get("makers", []) + ([r["contact"]] if isinstance(r.get("contact"), dict) else []):
                if s_.get("url") and not re.fullmatch(r"https?://\S+", str(s_["url"])):
                    errors.append(f"{w}: url malformed: {s_['url']}")
            ct = r.get("contact")
            if ct is not None and not isinstance(ct, dict):
                errors.append(f"{w}: contact must be a table [resource.contact]")
            elif ct is not None:
                if path.stem not in ("places", "events", "clubs") or not str(ct.get("url", "")).startswith("http") or not DATE.match(str(ct.get("date", ""))) \
                        or not any(ct.get(k) for k in ("address", "phone", "email")) or set(ct) - {"address", "phone", "email", "url", "date"}:
                    errors.append(f"{w}: contact (places, events, clubs) needs url, date YYYY-MM-DD and at least one of address, phone, email")
                if ct.get("phone") and not re.fullmatch(r"\+\d[\d ]{5,}\d", ct["phone"]):
                    errors.append(f"{w}: contact phone in international format (+33 4 90 00 00 00)")
                if ct.get("email") and not re.fullmatch(r"[\w.+-]+@[\w-]+(\.[\w-]+)*\.[a-z]{2,}", ct["email"], re.I):
                    errors.append(f"{w}: contact email malformed")
            for mk in r.get("makers", []):
                if not mk.get("id") and not mk.get("name_fr"):
                    errors.append(f"{w}: a maker without id needs name_fr (its name is a description)")
                if path.stem != "brands" or not mk.get("name") or not str(mk.get("url", "")).startswith("http") \
                        or mk.get("kind") not in KINDS - {"forum", "indexed"} or not DATE.match(str(mk.get("date", ""))):
                    errors.append(f"{w}: a maker needs name, url, date YYYY-MM-DD and kind official, read or third-party (brands only)")
        cats.append({"category": c, "resources": d.get("resource", [])})
    cats.sort(key=lambda x: ORDER.index(x["category"]["id"]) if x["category"].get("id") in ORDER else 99)
    alt = {r["id"] for c in cats if c["category"].get("id") == "brands" for r in c["resources"] if "official" not in r.get("covers", [])}
    for c in cats:
        for r in c["resources"]:
            w = f"{c['category'].get('id')}.toml: {r.get('id', '?')}"
            if "brands" in r and (c["category"].get("id") == "brands" or set(r["brands"]) - alt or len(set(r["brands"])) != len(r["brands"])):
                errors.append(f"{w}: brands must list ids of alternative brands of brands.toml, once each (not in brands.toml itself)")
            tp = {}
            for mk in r.get("makers", []):
                if mk.get("kind") == "third-party":
                    tp.setdefault(mk.get("id") or mk.get("name"), set()).add(re.sub(r"^https?://(www\.)?", "", str(mk.get("url", ""))).split("/")[0])
            for k, hosts in tp.items():
                if len(hosts) < 2 and not any(x.get("kind") == "official" and (x.get("id") or x.get("name")) == k for x in r.get("makers", [])):
                    errors.append(f"{w}: maker '{k}' rests on one third-party site: two independent sites are needed, or a statement of the brand or the maker")
            for mk in r.get("makers", []):
                if mk.get("id") and mk["id"] not in alt:
                    errors.append(f"{w}: maker id '{mk['id']}' is not an alternative brand of brands.toml")
    return cats, errors


notes = []  # breaches of the rules of lot 3 (writing, access, sizes, ranks): they fail the build
untranslated = []  # entries proposed in English only: warned, never refused; the monthly review adds the French texts


def text(r, key, lang):
    """A text of an entry in a language: the English one when the French translation is still missing."""
    return r.get(f"{key}_{lang}") if r.get("summary_" + lang) else r.get(f"{key}_en")


def access_context(cat, group):
    return ACCESS_GROUP.get((cat, group), ACCESS_CONTEXT.get(cat))


# French: "LEGO officiel" is a label only (filter, legend, heading); in a sentence, "de marque LEGO" for a product,
# "du groupe LEGO" for what the company runs, "sous enseigne LEGO" for a place run by a partner (decision of 24/11/2026, 10:13)
OFFICIEL = re.compile(r"\bLEGO\s+officiel(le)?s?\b|\bofficiel(le)?s?\s+LEGO\b")
# dates in texts: the month in letters, abbreviated (3 Jul 2027, 3 juil. 2027), never 2027-07-03 nor 03/07/2027 (decisions of 24/11/2026, 10:45, and 25/11/2026, 20:14)
NUMERIC_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{4}\b")
FULL_MONTH = re.compile(r"\b(?:\d{1,2}|1er) (?:January|February|March|April|June|July|August|September|October|November|December|janvier|février|avril|juillet|septembre|octobre|novembre|décembre)\b|\b(?:January|February|March|April|June|July|August|September|October|November|December|janvier|février|avril|juillet|septembre|octobre|novembre|décembre) \d{4}\b")
SUMMARY_WORDS = 35  # a card's text: what is particular, one or two sentences (decision of 12:28)
COUNTRY_WORDS = re.compile(r"^(?:an? |the )?(?:french|german|polish|italian|spanish|dutch|belgian|swiss|austrian|danish|swedish|norwegian|finnish|czech|slovak|british|english|scottish|welsh|irish|american|canadian|australian|chinese|japanese|portuguese|luxembourg\w*|south african|new zealand\w*|european|hungarian|greek|icelandic|estonian|latvian|lithuanian|slovenian|croatian|romanian|bulgarian|ukrainian|korean|taiwanese|brazilian|mexican)\b", re.I)
COUNTRY_WORDS_FR = re.compile(r"(?<!\ben )\b(?:français|allemand|polonais|italien|espagnol|néerlandais|belge|suisse|autrichien|danois|suédois|norvégien|finlandais|tchèque|slovaque|britannique|anglais|écossais|gallois|irlandais|américain|canadien|australien|chinois|japonais|portugais|luxembourgeois|sud-africain|néo-zélandais|européen|hongrois|grec|grecque|islandais|estonien|letton|lituanien|slovène|croate|roumain|bulgare|ukrainien|coréen|taïwanais|brésilien|mexicain)(?:ne|e)?s?\b", re.I)  # in French the demonym follows the noun: « Comparateur de prix allemand »; « en allemand » is a language
STOP = {"and", "the", "of", "for", "with", "official", "lego", "other", "brands", "brand", "sites", "site",
        "et", "les", "des", "pour", "avec", "officiel", "officiels", "autres", "marques", "marque", "sites"}


def text_notes(cats):
    """Writing rules of lot 3 on the texts of the entries (breaches go to notes)."""
    for c in cats:
        cid = c["category"]["id"]
        gname = {(g["id"], lang): g["name_" + lang] for g in c["category"].get("groups", []) for lang in LANGS}
        if OFFICIEL.search(c["category"].get("summary_fr", "")):
            notes.append(f"{cid}.toml: category summary_fr: « LEGO officiel » in a sentence")
        for r in c["resources"]:
            w = f"{cid}.toml: {r['id']}"
            for k, v in r.items():
                vs = v if isinstance(v, list) else [v]
                for x in vs:
                    if not isinstance(x, str):
                        continue
                    if k.endswith("_fr") and OFFICIEL.search(x):
                        notes.append(f"{w}: {k}: « {OFFICIEL.search(x).group(0)} » in a sentence: de marque LEGO (a product), du groupe LEGO (the company), sous enseigne LEGO (a partner)")
                    if (k.endswith("_en") or k.endswith("_fr")) and NUMERIC_DATE.search(x):
                        notes.append(f"{w}: {k}: date {NUMERIC_DATE.search(x).group(0)} with the month in letters")
                    if (k.endswith("_en") or k.endswith("_fr")) and re.search(r"(?<!\.)\.\.(?!\.)", x):
                        notes.append(f"{w}: {k}: double period")
                    if (k.endswith("_en") or k.endswith("_fr")) and FULL_MONTH.search(x):
                        notes.append(f"{w}: {k}: date « {FULL_MONTH.search(x).group(0)} » with the month abbreviated (Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec; janv. févr. mars avr. mai juin juil. août sept. oct. nov. déc.)")
            sm = r.get("summary_en", "")
            if len(sm.split()) > SUMMARY_WORDS or len(r.get("summary_fr", "").split()) > SUMMARY_WORDS:
                notes.append(f"{w}: summary of {max(len(sm.split()), len(r.get('summary_fr', '').split()))} words, {SUMMARY_WORDS} at most")
            for lang in ("en", "fr"):  # the group and the country, which the card shows, at the start of the text
                txt = r.get("summary_" + lang, "")
                first = [re.sub(r"s$", "", x) for x in re.findall(r"[a-zà-ÿ]+", txt.lower())[:4]]
                gw = {re.sub(r"s$", "", x) for x in re.findall(r"[a-zà-ÿ]+", gname.get((r["group"], lang), "").lower()) if len(x) > 3 and x not in STOP}
                if gw & set(first):
                    notes.append(f"{w}: summary_{lang} starts with its group ({', '.join(sorted(gw & set(first)))}): start with what sets the entry apart")
                if (COUNTRY_WORDS.search(txt) if lang == "en" else COUNTRY_WORDS_FR.search(" ".join(txt.split()[:6]))):
                    notes.append(f"{w}: summary_{lang} starts with a country: the card shows it")


def site_notes():
    """The same rule of the brand on the French sentences of the site: build.py (T, FEED_T) and site-src (strings.json
    except the strings marked as labels, French branches of app.js)."""
    for name, table in (("T", T), ("FEED_T", FEED_T)):
        for k, v in table.items():
            if isinstance(v, dict) and OFFICIEL.search(str(v.get("fr", ""))):
                notes.append(f"scripts/build.py: {name}[{k}]: « LEGO officiel » in a sentence")
    for k, v in json.loads(source("strings.json")).items():
        if not v.get("label") and OFFICIEL.search(v.get("fr", "")):
            notes.append(f"site-src/strings.json: {k}: « LEGO officiel » in a sentence (mark a label with \"label\": true)")
    for m in re.finditer(r"L===?'fr'\?(`[^`]*`|'[^']*')", source("app.js")):
        if OFFICIEL.search(m.group(1)):
            notes.append("site-src/app.js: « LEGO officiel » in a French sentence")


def rank_check(cats):
    """At most one entry per rank in a group and a scope."""
    for c in cats:
        seen = {}
        for r in c["resources"]:
            for k, v in (r.get("rank") or {}).items():
                seen.setdefault((r["group"], k, v), []).append(r["id"])
        for (g, k, v), ids_ in seen.items():
            if len(ids_) > 1:
                notes.append(f"{c['category']['id']}.toml: group {g}, scope {k}: rank {v} given to {', '.join(ids_)}")


def metrics():
    p = DATA / "metrics.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def regime(r, category):
    """activity: current while it posts, publishes or commits (a site, a channel, a forum, software);
    work: a finished work (book, article, guide, standard), dated, never inactive for its age;
    operating: open or closed (a place, a shop, a brand, a club), checked by the review, not by its posts."""
    group = next((g for g in category.get("groups", []) if g["id"] == r.get("group")), {})
    return r.get("regime") or group.get("regime") or "activity"


def effective(r, m):
    """Status and last activity, after automatic metrics (data/metrics.json)."""
    last = str(r.get("last_activity") or "")
    auto = m.get(r["id"], {}).get("last_activity")
    if auto and auto > last:
        last = auto
    status = r["status"]
    if r.get("_regime", "activity") != "activity":
        return status, last  # declared: active, archived or dead
    if status in ("active", "slow", "inactive") and last:
        days = (dt.date.today() - dt.date.fromisoformat(last)).days
        status = "active" if days <= 183 else "slow" if days <= 365 else "inactive"
    if status in ("slow", "inactive") and str(r.get("next_date") or "") >= dt.date.today().isoformat():
        status = "active"  # a recurring event with an announced next edition is alive between editions
    return status, last


def anchor(s):
    return re.sub(r"[^\w -]", "", s.lower().replace("’", "").replace("'", "")).strip().replace(" ", "-")  # as GitHub: letters with accents stay (« cafés »)


FILES = {("readme", "en"): "README.md", ("full", "en"): "full-list.md"}
MORE = {"readme": {"en": "Only the best of each group is listed here. The [full list](full-list.md) has every resource, including inactive and dead ones."},
        "full": {"en": "Every resource, including inactive and dead ones, generated from [`data/`](data/). The selection of the best is in the [README](README.md)."}}


def readme(cats, lang, kind="readme"):
    title = T["title"][lang] if kind == "readme" else "Awesome LEGO: full list"
    badge = " [![Awesome](https://awesome.re/badge.svg)](https://awesome.re)" if kind == "readme" else ""
    keep = picked if kind == "readme" else (lambda r: True)
    logo = [f'<a href="{PAGES}"><img src="media/logo.svg" align="right" width="120" alt="Awesome LEGO logo"></a>', ""] if kind == "readme" else []
    out = [f"# {title}{badge}", "", *logo, f"> {T['tagline'][lang]}", "",
           f"**[{T['site'][lang]}]({PAGES})** · [{T['site_fr'][lang]}]({PAGES}fr/) · [{T['feed'][lang]}]({PAGES}feed.xml)", "",
           *([f'<p align="center"><a href="{PAGES}"><picture><source media="(prefers-color-scheme: dark)" srcset="media/site-preview-dark.png"><img src="media/site-preview.png" width="880" alt="The website: Where to start, one card per need with its best resources, beside the map of the brick world, one stud per resource by category"></picture></a></p>', ""] if kind == "readme" else []),
           MORE[kind][lang], "", f"## {T['contents'][lang]}", ""]
    seen = {}

    def icon(cid):
        return f'<img src="media/icons/heading/{cid}.svg" width="40" height="56" align="left" hspace="4" alt="">' if (ROOT / "media" / "icons" / "heading" / f"{cid}.svg").exists() else ""  # heading/: same icons with a transparent top margin, so the floated icon lines up with the heading text

    def uniq(name):  # GitHub suffixes repeated heading anchors with -1, -2…
        a = anchor(name)
        n = seen.get(a, 0)
        seen[a] = n + 1
        return a if n == 0 else f"{a}-{n}"
    uniq(T["contents"][lang])
    shown, listed = {}, set()  # entries of each group; the README gives a link once (awesome-lint: double-link), the full list every entry
    for c in cats:
        for g in c["category"].get("groups", []):
            rs = [r for r in c["resources"] if r["group"] == g["id"] and keep(r) and (kind != "readme" or r["url"] not in listed)]
            listed.update(r["url"] for r in rs)
            shown[(c["category"]["id"], g["id"])] = rs
    has = lambda c: any(shown[(c["category"]["id"], g["id"])] for g in c["category"].get("groups", []))
    for c in cats:
        if not has(c):
            continue
        name = c["category"][f"name_{lang}"]
        out.append(f"- [{name}](#{uniq(name)})")
        for g in c["category"].get("groups", []):
            if shown[(c["category"]["id"], g["id"])]:
                out.append(f"  - [{g['name_' + lang]}](#{uniq(g['name_' + lang])})")
    for c in cats:
        cat = c["category"]
        if not has(c):
            continue
        # the icon floats left of the heading: inside the heading, awesome-lint and GitHub disagree on its anchor
        out += ["", "<br>", "", *([icon(cat["id"]), ""] if icon(cat["id"]) else []), f"## {cat['name_' + lang]}", ""]
        if cat.get("summary_" + lang):
            out += [cat["summary_" + lang], ""]
        for g in cat.get("groups", []):
            rs = shown[(cat["id"], g["id"])]
            if not rs:
                continue
            out += [f"### {g['name_' + lang]}", ""]
            for r in sorted(rs, key=lambda r: r["name"].lower()):
                status = r["status"]  # declared status: generated files stay stable between data changes
                worlds = [w for k, w in (("official", "official LEGO"), ("alternative", "alternative brands")) if k in r.get("covers", [])]
                marks = (f"Covers {' and '.join(worlds)}." if worlds else "")
                if r.get("audience"):  # the publics the entry states (data/SCHEMA.md, audience)
                    marks += (" " if marks else "") + "For " + " and ".join(a for a in AUDIENCES if a in r["audience"]) + "."
                if status != "active":
                    marks += " Status: " + {"slow": "no update for 6 months", "inactive": "no update for a year"}.get(status, status) + "."
                desc = r["summary_" + lang].strip()
                if kind == "readme":  # awesome style: one short sentence
                    parts = re.split(r"(?<=[a-z0-9)])\.\s+(?=[A-Z])", desc)
                    desc = parts[0] if len(parts[0]) >= 45 or len(parts) == 1 else parts[0] + ". " + parts[1]  # "Denmark." alone says too little
                if not desc.endswith("."):
                    desc += "."
                out.append(f"- [{r['name']}]({r['url']}) - {desc}{(' ' + marks.strip()) if marks.strip() else ''}")
            out.append("")
    out += [f"## {T['contributing'][lang]}", "", T["contrib_text"][lang], ""]
    return "\n".join(out).replace("\n\n\n", "\n\n")


def alt_brands(cats):
    """Alternative brands of brands.toml with every name they go by: the name, the names in brackets
    ('Lumibricks (formerly Funwhole)', 'Keeppley (Qman)') and `aliases`. They feed the search suggestions."""
    out = []
    for c in cats:
        if c["category"]["id"] != "brands":
            continue
        for r in c["resources"]:
            if "official" in r.get("covers", []):
                continue
            main = re.sub(r"\s*\(.*?\)", "", r["name"]).strip()
            extra = [re.sub(r"^(formerly|with) ", "", x).strip() for x in re.findall(r"\(([^)]+)\)", r["name"])]
            out.append({"id": r["id"], "name": main, "aka": [n for n in dict.fromkeys(extra + r.get("aliases", [])) if n and n != main]})
    return out


def site_data(cats, m):
    rows = []
    by_host = {}
    for c in cats:
        for r in c["resources"]:
            by_host.setdefault(host(r["url"]), []).append(r["id"])
    same = {h: ids_ for h, ids_ in by_host.items() if len(ids_) > 1 and not PLATFORMS.search(h)}  # "From the same site"
    for c in cats:
        cat = c["category"]
        gnames = {g["id"]: {lang: g.get("short_" + lang) or g["name_" + lang] for lang in LANGS} for g in cat.get("groups", [])}  # card labels
        for r in c["resources"]:
            status, last = effective(r, m)
            row = {k: r.get(k) for k in ("id", "name", "url", "covers", "languages", "countries", "confidence", "checked", "github", "subreddit", "city", "city_fr", "city_local", "ships_to_france", "rank", "size", "audience")}
            row = {k: v for k, v in row.items() if v is not None}
            row["featured"] = picked(r)  # the selection: rank 1 worldwide of its group (★, filter, README)
            ctx = access_context(cat["id"], r["group"])
            row["access"] = f"{ctx}_{r['access']}" if r.get("access") in ACCESS_BY.get(ctx, set()) else None  # label of strings.json
            row["operator"] = r.get("operator")  # sites and places of the LEGO Group (lego-group) or under the LEGO brand by a partner (licensee)
            row["same"] = same.get(host(r["url"]), [])
            if cat["id"] == "brands":  # logo of the brand, from its official site (media/logos/, licence apart in REUSE.toml)
                row["logo"] = next((f"media/logos/{r['id']}.{x}" for x in ("svg", "png") if (ROOT / "media" / "logos" / f"{r['id']}.{x}").exists()), None)
            row["next"] = str(r["next_date"]) if r.get("next_date") and str(r["next_date"]) >= dt.date.today().isoformat() else None  # past dates are dropped at each daily build
            row.update(cat=cat["id"], group=r["group"], status=status, last=last, regime=r["_regime"],
                       metrics=m.get(r["id"], {}),
                       sources=[{"url": s["url"], "date": str(s["date"]), "kind": s["kind"]} for s in r.get("sources", [])])
            for lang in LANGS:
                row[lang] = {"summary": text(r, "summary", lang), "strengths": text(r, "strengths", lang) or [],
                             "weaknesses": text(r, "weaknesses", lang) or [],
                             "group": gnames.get(r["group"], {}).get(lang, r["group"]),
                             **({"rec": text(r, "recurrence", lang)} if text(r, "recurrence", lang) else {}),
                             **({} if r.get("summary_" + lang) else {"tl": "en"})}  # the French page shows the English text, marked as such
            row["checked"] = str(row["checked"])
            row["brands"] = r.get("brands", [])  # read at the source of each entry (brands of brands.toml it sells, tracks, reviews or admits)
            row["funding"] = r.get("funding")
            if r.get("contact"):
                row["contact"] = {k: r["contact"][k] for k in ("address", "phone", "email") if r["contact"].get(k)}
            if r.get("makers"):
                row["makers"] = [{k: str(x[k]) for k in ("name", "name_fr", "id", "url", "date", "kind") if x.get(k)} for x in r["makers"]]
            rows.append(row)
    categories = [{"id": c["category"]["id"], "en": c["category"]["name_en"], "fr": c["category"]["name_fr"],
                   "summary": {lang: c["category"].get("summary_" + lang, "") for lang in LANGS},
                   "groups": [{"id": g["id"], "en": g["name_en"], "fr": g["name_fr"]} for g in c["category"].get("groups", [])]} for c in cats]
    ids = {r["id"] for r in rows}
    journeys = needs(cats, ids)
    return {"built": dt.date.today().isoformat(), "categories": categories, "resources": rows, "journeys": journeys,
            "brands": alt_brands(cats), "passion": passion()}


def needs(cats, ids):
    """data/journeys.toml: the needs of "Where to start", checked against the data."""
    js = tomllib.loads((DATA / "journeys.toml").read_text(encoding="utf-8")).get("need", [])
    groups = {f"{c['category']['id']}/{g['id']}" for c in cats for g in c["category"].get("groups", [])}
    cids = {c["category"]["id"] for c in cats}
    bad = []
    for j in js:
        w = f"journeys.toml: {j.get('id')}"
        if not (j.get("id") and j.get("title_en") and j.get("title_fr")):
            bad.append(f"{w}: id, title_en and title_fr needed")
        if j.get("category") not in cids:
            bad.append(f"{w}: category must be a category id (its icon and its link)")
        if not j.get("groups") or set(j["groups"]) - groups:
            bad.append(f"{w}: groups must be <category>/<group> ids: {sorted(set(j.get('groups', [])) - groups)}")
        if j.get("scope") not in RANK_SCOPES:
            bad.append(f"{w}: scope must be one of {sorted(RANK_SCOPES)}")
        if j.get("icon") is not None and not (ROOT / "media" / "icons" / f"{j['icon']}.svg").exists():
            bad.append(f"{w}: icon must name a file of media/icons/ (without .svg)")
        if j.get("audience") not in (None, *AUDIENCES):
            bad.append(f"{w}: audience must be one of {list(AUDIENCES)}")
        if j.get("mode") not in (None, "brand"):
            bad.append(f"{w}: mode can only be brand")
        code = {"country": r"[A-Z]{2}", "language": r"[a-z]{2}"}.get(j.get("scope"), r"(?!)")
        for k, v in (j.get("reference") or {}).items():
            if not (k == "default" or re.fullmatch(code, k)):
                bad.append(f"{w}: reference key {k} is a {j.get('scope')} code or default")
            if v not in ids:
                bad.append(f"{w}: unknown resource {v}")
        if set(j) - {"id", "title_en", "title_fr", "category", "icon", "groups", "scope", "mode", "audience", "reference"}:
            bad.append(f"{w}: unknown keys {sorted(set(j) - {'id', 'title_en', 'title_fr', 'category', 'icon', 'groups', 'scope', 'mode', 'audience', 'reference'})}")
    if bad:
        fail(bad)
    return js


PLATFORMS = re.compile(r"(^|\.)(youtube\.com|youtu\.be|reddit\.com|github\.com|spotify\.com|wikipedia\.org)$")  # one site, many unrelated pages


def host(url):
    return re.sub(r"^www\.", "", re.sub(r"^https?://", "", url).split("/")[0].lower())


def picked(r):
    """The selection (★, README, filter, suggestions): the rank 1 worldwide of each group (lot 3b; `featured` before)."""
    return (r.get("rank") or {}).get("intl") == 1


def passion():
    """Recognized fan communities per country against population (backend data, not shown as entries)."""
    cf, pf = DATA / "backend" / "clubs-by-country.json", DATA / "backend" / "population.json"
    if not (cf.exists() and pf.exists()):
        return None
    c, p = json.loads(cf.read_text(encoding="utf-8")), json.loads(pf.read_text(encoding="utf-8"))
    return {"source": c["source"], "date": c["date"], "pop_source": p["source"], "pop_year": p["year"],
            "rows": [{"c": k, "n": n, "pop": p["population"].get(k)} for k, n in c["countries"].items()]}


SRC = ROOT / "site-src"


def source(name):
    """A part of the page from site-src/, as it goes into the template: without its final newline."""
    text = (SRC / name).read_text(encoding="utf-8")
    return text[:-1] if text.endswith("\n") else text


def assemble():
    """The page template, put together from its parts: index.html (skeleton, head scripts, vault hint script),
    style.css, app.js (the page's script) and strings.json (interface strings in English and French, the table S
    of app.js), plus the shared header (header.html, header.js). Plain text insertion, no modules: the page served is one file per language, as before."""
    return shared((SRC / "index.html").read_text(encoding="utf-8")).replace("{{APP}}", source("app.js").replace("{{STRINGS}}", source("strings.json"), 1), 1)


def shared(tpl):
    """The parts every page of the website shares: style.css, the header (header.html) and its script (header.js), the footer
    with the hidden way to the Brick Vault (footer.html). Their placeholders: HOME (the directory page of the language), ROOT
    (the root of the website), ABOUT and ABOUTCUR (the about page, and the mark of the current page on it)."""
    return (tpl.replace("{{STYLE}}", source("style.css"), 1).replace("{{HEADER}}", source("header.html"), 1).replace("{{HEADERJS}}", source("header.js"), 1)
            .replace("{{FOOTER}}", source("footer.html"), 1))


def static_texts(tpl, lang):
    """Fill the empty elements marked data-t="key" with the string the page's script would put there
    (site-src/strings.json): the first paint shows the final texts, nothing moves after."""
    S = {k: v[lang] for k, v in json.loads(source("strings.json")).items()}
    tpl = re.sub(r'\bdata-t-label="(\w+)"', lambda m: m.group(0) + f' aria-label="{html.escape(S[m.group(1)])}"' if m.group(1) in S else m.group(0), tpl)  # names of the icon buttons, for pages without app.js
    return re.sub(r'(<(\w+)\b[^>]*\bdata-t="(\w+)"[^>]*>)(</\2>)',
                  lambda m: m.group(1) + html.escape(S[m.group(3)], quote=False) + m.group(4) if m.group(3) in S else m.group(0), tpl)


PAGE_UNREAD = {"confidence", "github", "subreddit"}  # in data.json for the scripts, never read by the page


def page_texts(x):
    """The texts of an entry carried by the page; strengths and weaknesses go to details.json, read when needed."""
    return {**{k: v for k, v in x.items() if k not in ("strengths", "weaknesses", "rec")}, "d": bool(x["strengths"] or x["weaknesses"])}


def details(lang, data):
    """site/details.json and site/fr/details.json: strengths and weaknesses of each entry, [strengths, weaknesses]."""
    return json.dumps({r["id"]: [r[lang]["strengths"], r[lang]["weaknesses"]] for r in data["resources"] if r[lang]["strengths"] or r[lang]["weaknesses"]},
                      ensure_ascii=False, separators=(",", ":"))


def page(lang, data):
    tpl = static_texts(assemble(), lang)
    other = "fr/" if lang == "en" else "../"
    lean = dict(data, resources=[{**{k: v for k, v in r.items() if k not in LANGS and k not in PAGE_UNREAD and not (v is None or v is False or v == [] or v == {})}, lang: page_texts(r[lang])}
                                 for r in data["resources"]])  # each page carries its own language only, without what app.js never reads nor empty values (read as absent)
    blob = json.dumps(lean, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")  # no "</script" nor "<!--" inside the data block
    values = {"LANG": lang, "OTHER": other, "TITLE": html.escape(T["title"][lang]), "TAGLINE": html.escape(T["site_tagline"][lang]),
              "MINISEARCH": (ROOT / "site-src" / "vendor" / "minisearch.min.js").read_text(encoding="utf-8"),
              "FEEDTITLE": html.escape(FEED_T["title"][lang]), "FEEDPATH": "fr/" if lang == "fr" else "",
              "DATA": blob, "REPO": REPO, "VERSION": data["version"], "CSP": "{{CSP}}", "BRAND": "#top", "HOME": "", "ABOUT": "about/", "ABOUTCUR": "", "ROOT": "../" if lang == "fr" else ""}
    out = re.sub(r"\{\{(\w+)\}\}", lambda m: values[m.group(1)], tpl)  # one pass: a text of the data that contains {{…}} is never replaced again
    i = out.index("{{CSP}}")  # the policy is the template's own placeholder, before any data
    return out[:i] + csp(out) + out[i + len("{{CSP}}"):]


class _Scripts(html.parser.HTMLParser):
    """Bodies of the executable inline scripts (<script> without attributes), read by an HTML parser."""
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.bodies, self._in = [], False

    def handle_starttag(self, tag, attrs):
        if tag == "script" and not attrs:
            self._in = True
            self.bodies.append("")

    def handle_endtag(self, tag):
        if tag == "script":
            self._in = False

    def handle_data(self, data):
        if self._in:
            self.bodies[-1] += data


def inline_scripts(doc):
    p = _Scripts()
    p.feed(doc)
    p.close()
    return p.bodies


def csp(doc, rest="; style-src 'unsafe-inline'; img-src 'self' https://actarus314.github.io; connect-src 'self'; base-uri 'none'; form-action 'none'"):
    """Content security policy (GitHub Pages sends no headers: a meta element, placed before the first script).
    Only the page's own inline scripts run, each allowed by its hash; nothing is loaded from elsewhere."""
    hashes = [base64.b64encode(hashlib.sha256(m.encode("utf-8")).digest()).decode()
              for m in inline_scripts(doc)]
    return "default-src 'none'; script-src " + " ".join(f"'sha256-{h}'" for h in hashes) + rest


ABOUT_PATH = {"en": "about/", "fr": "fr/about/"}


def about(lang, data):
    """site/about/ and site/fr/about/: what the directory is, how it is made and kept current, why a selection and how
    it is made, how to take part. Plain text that search engines read without running the page's script;
    its figures come from the data at each build. Texts in site-src/about.json, page in about.html, styles in about.css."""
    A = {k: v[lang] for k, v in json.loads(source("about.json")).items()}
    R = data["resources"]
    n, ranked, sel = len(R), sum(1 for r in R if r.get("rank")), sum(1 for r in R if r["featured"])
    groups = sum(len(c["groups"]) for c in data["categories"])
    home = "../"  # the directory page of the same language: site/ from site/about/, site/fr/ from site/fr/about/
    fill = lambda x: x.replace("{REPO}", REPO).replace("{HOME}", home).replace("{groups}", str(groups)).replace("{active}", str(sum(1 for r in R if r["status"] == "active"))).replace("{date}", in_letters(data["built"], lang))
    canon = PAGES + ABOUT_PATH[lang]
    ld = json.dumps({"@context": "https://schema.org", "@type": "AboutPage", "name": A["ptitle"], "description": A["pdesc"], "url": canon,
                     "inLanguage": lang, "dateModified": data["built"], "isPartOf": {"@type": "WebSite", "name": "Awesome LEGO", "url": PAGES + ("fr/" if lang == "fr" else "")}},
                    ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    pct = lambda k: f"{max(1, round(100 * k / n))}%"
    values = {"LANG": lang, "PTITLE": html.escape(A["ptitle"]), "PDESC": html.escape(A["pdesc"]), "CANON": canon, "LD": ld,
              "FEEDTITLE": html.escape(FEED_T["title"][lang]), "FEEDPATH": "fr/" if lang == "fr" else "", "ASTYLE": source("about.css"),
              "REPO": REPO, "VERSION": data["version"], "CSP": "{{CSP}}", "BRAND": home, "HOME": home, "ABOUT": "./", "ABOUTCUR": ' aria-current="page"', "ROOT": "../../" if lang == "fr" else "../",
              "OTHER": "../fr/about/" if lang == "en" else "../../about/",
              "N": str(n), "RANKED": str(ranked), "SEL": str(sel), "RANKEDW": pct(ranked), "SELW": pct(sel),
              "COUNTRIES": str(len({c for r in R for c in r.get("countries") or [] if c != "international"})),
              "LANGS": str(len({x for r in R for x in r.get("languages") or []})), "SOURCES": str(sum(len(r["sources"]) for r in R))}
    tpl = static_texts(shared((SRC / "about.html").read_text(encoding="utf-8")), lang)
    tpl = re.sub(r"\{\{a:(\w+)\}\}", lambda m: fill(A[m.group(1)]), tpl)  # the page's own texts: trusted HTML of site-src/about.json
    out = re.sub(r"\{\{(\w+)\}\}", lambda m: values[m.group(1)], tpl)
    i = out.index("{{CSP}}")
    return out[:i] + csp(out) + out[i + len("{{CSP}}"):]


def vault():
    """The Brick Vault (site/vault/): an English-only easter egg that the Konami code opens from either home page.
    Its fonts are served by the site itself (media/fonts/, SIL Open Font License); it contacts nothing else."""
    doc = (ROOT / "site-src" / "vault.html").read_text(encoding="utf-8")
    return doc.replace("{{CSP}}", csp(doc, "; style-src 'unsafe-inline'; font-src 'self'; img-src 'self'; connect-src 'none'; base-uri 'none'; form-action 'none'"))


BASELINE = "2026-11-23"  # the directory's first day: its entries make one opening item, not 400 separate ones
FEED_BATCH = 20  # more entries added on one day make one announcement, like the opening (lot 3b)
FEED_T = {
    "title": {"en": "Awesome LEGO", "fr": "Awesome LEGO"},  # the feed is named after the website (request of 26/11/2026)
    "new": {"en": "New", "fr": "Nouveau"},
    "open": {"en": "Awesome LEGO opens with {n} resources", "fr": "Awesome LEGO ouvre avec {n} ressources"},
    "batch": {"en": "{n} resources added to the directory", "fr": "{n} ressources ajoutées à l'annuaire"},
    "batch_body": {"en": "Added on {date}, each checked at its source: {cats}.", "fr": "Ajoutées le {date}, chacune vérifiée à sa source : {cats}."},
    "open_body": {"en": "{n} resources of the brick world, each checked at its source: brands, shops, prices, second-hand, communities, videos, events, places, clubs, learning and tools.",
                  "fr": "{n} ressources du monde de la brique, chacune vérifiée à sa source : marques, boutiques, prix, occasion, communautés, vidéos, événements, lieux, clubs, apprendre et outils."},
}


def atom(title, self_url, site_url, items):
    """items: (id, title, link, date, text), newest first."""
    esc = lambda x: html.escape(str(x).strip(), quote=True)
    entries = "".join(f"<entry><title>{esc(t)}</title><id>{esc(i)}</id><link href=\"{esc(l)}\"/><updated>{d}T00:00:00Z</updated>"
                      f"<content type=\"text\">{esc(x)}</content></entry>" for i, t, l, d, x in items)
    updated = items[0][3] if items else dt.date.today().isoformat()
    return (f'<?xml version="1.0" encoding="utf-8"?><feed xmlns="http://www.w3.org/2005/Atom"><title>{esc(title)}</title>'
            f'<id>{self_url}</id><link href="{site_url}"/><link rel="self" href="{self_url}"/>'
            f'<icon>{PAGES}media/favicon.png</icon><logo>{PAGES}media/apple-touch-icon.png</logo>'
            f'<updated>{updated}T00:00:00Z</updated><author><name>Awesome LEGO</name></author>{entries}</feed>\n')


MONTHS = {"en": "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(),  # months abbreviated everywhere (decision of 25/11/2026, 20:14)
          "fr": "janv. févr. mars avr. mai juin juil. août sept. oct. nov. déc.".split()}


def in_letters(iso, lang):
    """2027-07-03: 3 Jul 2027, 3 juil. 2027; the first of the month in French: 1er avr. 2027."""
    y, m, d = (int(x) for x in iso.split("-"))
    return f"{'1er' if lang == 'fr' and d == 1 else d} {MONTHS[lang][m - 1]} {y}"


def content_feed(cats, lang):
    """What readers follow: entries added to the directory, in one language (no event dates: the calendar was removed in v3.0)."""
    site = PAGES + ("fr/" if lang == "fr" else "")
    items, base, days = [], 0, {}
    for c in cats:
        for r in c["resources"]:
            if str(r["added"]) > BASELINE:
                days.setdefault(str(r["added"]), []).append(c["category"]["name_" + lang])
    for c in cats:
        cname = c["category"]["name_" + lang]
        for r in c["resources"]:
            link = f"{site}#entry={r['id']}"
            if str(r["added"]) <= BASELINE:
                base += 1
            elif len(days[str(r["added"])]) <= FEED_BATCH:
                items.append((f"{site}#added-{r['id']}", f"{FEED_T['new'][lang]} · {cname} · {r['name']}", link, str(r["added"]), text(r, "summary", lang)))
    for day, names in days.items():
        if len(names) > FEED_BATCH:
            per = ", ".join(f"{n} {sum(1 for x in names if x == n)}" for n in dict.fromkeys(names))
            items.append((f"{site}#added-{day}", FEED_T["batch"][lang].format(n=len(names)), site, day,
                          FEED_T["batch_body"][lang].format(date=in_letters(day, lang), cats=per)))
    if base:
        items.append((f"{site}#opening", FEED_T["open"][lang].format(n=base), site, BASELINE, FEED_T["open_body"][lang].format(n=base)))
    items.sort(key=lambda x: (x[3], x[1]), reverse=True)
    return atom(FEED_T["title"][lang], site + "feed.xml", site, items[:60])


def changes_feed():
    """For whoever follows the development: one item per version, from CHANGELOG.md."""
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    found = re.findall(r"(?m)^## v(\d+\.\d+) — (\d{4}-\d{2}-\d{2})\n(.*?)(?=^## v|^# v|\Z)", text, re.S)[:30]
    items = [(f"https://github.com/{REPO}/releases/tag/v{v}", f"v{v}", f"https://github.com/{REPO}/releases/tag/v{v}", d, body) for v, d, body in found]
    return atom("Awesome LEGO: changes", PAGES + "changes.xml", f"https://github.com/{REPO}", items)


def issue_form(cats):
    """The "Add a resource" form, with the category list taken from the data."""
    path = ROOT / ".github" / "ISSUE_TEMPLATE" / "add-resource.yml"
    text = path.read_text(encoding="utf-8")
    opts = "".join(f"        - {c['category']['name_en']}\n" for c in cats)
    return re.sub(r"(label: Category\n      options:\n)(?:        - [^\n]*\n)+", lambda m: m.group(1) + opts, text, count=1)


README_IMAGES = ("site-preview.png", "site-preview-dark.png")  # written by scripts/readme_image.py


def png_text(path, key):
    """The value of a text chunk of a PNG (tEXt), or None."""
    b = path.read_bytes()
    i = 8
    while i + 8 <= len(b):
        n, kind = int.from_bytes(b[i:i + 4], "big"), b[i + 4:i + 8]
        if kind == b"tEXt":
            k, _, v = b[i + 8:i + 8 + n].partition(b"\0")
            if k.decode("latin-1") == key:
                return v.decode("latin-1")
        if kind == b"IEND":
            break
        i += 12 + n
    return None


def check_readme_images(version):
    """The README image shows the current version: the workflow Version takes it again when it raises VERSION (a warning)."""
    errors = []
    for name in README_IMAGES:
        f = ROOT / "media" / name
        shown = png_text(f, "version") if f.exists() else None
        if shown != version:
            errors.append(f"media/{name} shows v{shown or '?'}, VERSION is {version}: the pull request of Version takes it again; by hand: python3 scripts/build.py --site-only && python3 scripts/readme_image.py")
    return errors


def check_docs():
    """The documents that describe the data and the automation must name what exists."""
    errors = []
    schema = (DATA / "SCHEMA.md").read_text(encoding="utf-8")
    for name, words in (("covers", COVERS), ("access", ACCESS), ("status", STATUS), ("regime", REGIMES), ("kind", KINDS), ("funding", FUNDING)):
        line = next((l for l in schema.splitlines() if l.startswith(f"{name} = ")), "")
        missing = sorted(w for w in words if not re.search(rf"\b{re.escape(w)}\b", line))
        if missing:
            errors.append(f"data/SCHEMA.md: the `{name}` line does not list {', '.join(missing)}")
    S = json.loads(source("strings.json"))  # one table of labels for the website
    need = [f"acc_{c}_{v}" for c, vs in ACCESS_BY.items() for v in sorted(vs)] + [k for u in sorted(UNITS) for k in (f"u_{u}", f"u_{u}1")] + [f"sz_{a}" for a in sorted(APPROX)]
    errors += [f"site-src/strings.json: label {k} missing" for k in need if not (S.get(k, {}).get("en") and S.get(k, {}).get("fr"))]
    sizes = next((l for l in schema.splitlines() if l.startswith("Sizes (")), "")
    errors += [f"data/SCHEMA.md: the Sizes line does not list {u}" for u in sorted(UNITS) if not re.search(rf"\b{re.escape(u)}\b", sizes)]
    for f in sorted((DATA / "backend").glob("*.json")):
        if f"`{f.name}`" not in schema:
            errors.append(f"data/SCHEMA.md: data/backend/{f.name} is not described")
    maint = (ROOT / "MAINTENANCE.md").read_text(encoding="utf-8")
    for wf in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        y = wf.read_text(encoding="utf-8")
        name = re.search(r"(?m)^name: (.+)$", y).group(1).strip()
        if f"**{name}**" not in maint:
            errors.append(f"MAINTENANCE.md: workflow **{name}** ({wf.name}) is not described")
        for mi, h in re.findall(r'cron: "(\d+) (\d+) ', y):
            if f"{int(h):02d}:{int(mi):02d}" not in maint:
                errors.append(f"MAINTENANCE.md: the time {int(h):02d}:{int(mi):02d} of **{name}** is missing")
    return errors


def report_notes():
    """The breaches of the rules of lot 3 fail the build."""
    if notes:
        fail(notes)


CHANGELOG_MAX = 550  # rule of a changelog entry: about 250 characters, 550 at most when dense with facts


def changelog_long(text):
    """The paragraphs of CHANGELOG.md entries longer than CHANGELOG_MAX, as "vX.Y: n characters". An entry assembled
    by the workflow Version has one paragraph per fragment of changes/ (scripts/changes.py)."""
    return [f"v{v}: {len(para.strip())} characters" for v, body in re.findall(r"(?m)^## v(\d+\.\d+) — [\d-]+\n(.*?)(?=^## v|^# v|\Z)", text, re.S)
            for para in body.split("\n\n") if len(para.strip()) > CHANGELOG_MAX]


def out_of_date(stale, waiting, mode):
    """(errors, warnings) for generated files out of date. waiting: the types of the fragments of changes/.
    mode "pull-request" (Check on a pull request other than Version's): a warning whatever main holds, the workflow
    Version rebuilds them after the merge (scripts/changes.py says when a fragment is missing); "strict" (the pull
    request of Version): an error; "" (main, or a local run): a warning while a fragment waits, an error otherwise."""
    if not stale or mode == "strict" or (mode != "pull-request" and not waiting):
        return [f"{f} is out of date: a pull request leaves it to the Version workflow and adds changes/<name>.md (contributing.md); "
                "on main, start Version by hand (MAINTENANCE.md)" for f in stale], []
    when = ("by the next pull request vX.Y" if set(waiting) - {"none"} else
            "with the next version: only fragments of type none wait, so nothing is numbered yet (Version started by hand rebuilds it now)")
    return [], [f"{f} is out of date: the Version workflow rebuilds it {when}" for f in stale]


def waiting_types():
    """Types of the fragments of changes/ (their first line; scripts/changes.py checks them)."""
    return [f.read_text(encoding="utf-8-sig").partition("\n")[0].removeprefix("type:").strip() for f in sorted((ROOT / "changes").glob("*.md")) if f.is_file()]


def main():
    cats, errors = load()
    errors += check_docs()
    if errors:
        fail(errors)
    rank_check(cats)
    text_notes(cats)
    site_notes()
    m = metrics()
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not re.search(rf"^## v{re.escape(version)} — \d{{4}}-\d{{2}}-\d{{2}}$", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), re.M):
        fail([f"CHANGELOG.md has no '## v{version} — YYYY-MM-DD' section for VERSION {version}"])
    long = changelog_long((ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))
    if long:  # one short entry per version; the details belong to the pull request
        fail([f"CHANGELOG.md entry longer than {CHANGELOG_MAX} characters ({x}): say what changes in two sentences" for x in long])
    for w in check_readme_images(version) if "--check" in sys.argv else []:  # a warning, never an error: decision of 25/11/2026
        print("! " + w)
    texts = {f: readme(cats, lang, kind) for (kind, lang), f in FILES.items()}
    texts[".github/ISSUE_TEMPLATE/add-resource.yml"] = issue_form(cats)
    print(f"✓ v{version}: {sum(len(c['resources']) for c in cats)} resources in {len(cats)} categories")
    if untranslated:  # a warning, never an error: contributions come in English only
        print(f"! French translation missing for {len(untranslated)} entries (the monthly review adds it): " + ", ".join(x.split(": ")[1] for x in untranslated))
    report_notes()
    if "--check" in sys.argv:
        stale = [f for f, t in texts.items() if not (ROOT / f).exists() or (ROOT / f).read_text(encoding="utf-8") != t]
        mode = "strict" if "--strict" in sys.argv else "pull-request" if "--pull-request" in sys.argv else ""
        errors, warnings = out_of_date(stale, waiting_types(), mode)
        for w in warnings:
            print("! " + w)
        if errors:
            fail(errors)
        return
    if "--site-only" not in sys.argv:
        for f, t in texts.items():
            (ROOT / f).write_text(t, encoding="utf-8")
        print("✓ " + ", ".join(texts))
    data = site_data(cats, m)
    data["version"] = version
    (SITE / "fr").mkdir(parents=True, exist_ok=True)
    (SITE / "index.html").write_text(page("en", data), encoding="utf-8")
    (SITE / "fr" / "index.html").write_text(page("fr", data), encoding="utf-8")
    (SITE / "details.json").write_text(details("en", data), encoding="utf-8")
    (SITE / "fr" / "details.json").write_text(details("fr", data), encoding="utf-8")
    for lang, path in ABOUT_PATH.items():
        (SITE / path).mkdir(parents=True, exist_ok=True)
        (SITE / path / "index.html").write_text(about(lang, data), encoding="utf-8")
    (SITE / "vault").mkdir(parents=True, exist_ok=True)
    (SITE / "vault" / "index.html").write_text(vault(), encoding="utf-8")
    (SITE / "feed.xml").write_text(content_feed(cats, "en"), encoding="utf-8")
    (SITE / "fr" / "feed.xml").write_text(content_feed(cats, "fr"), encoding="utf-8")
    (SITE / "changes.xml").write_text(changes_feed(), encoding="utf-8")
    (SITE / "favicon.ico").write_bytes((ROOT / "media" / "favicon.ico").read_bytes())  # readers that look for <site>/favicon.ico
    for f in (ROOT / "media").rglob("*"):
        if f.is_file() and f.name not in README_IMAGES:  # the README image is read on GitHub, not on the website
            out = SITE / f.relative_to(ROOT)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(f.read_bytes())
    (SITE / "data.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")  # read by scripts/refresh.py --from-site
    print("✓ site/index.html, site/fr/index.html, site/about/, site/fr/about/, site/data.json")


if __name__ == "__main__":
    main()
