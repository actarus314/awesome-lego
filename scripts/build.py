#!/usr/bin/env python3
"""Validate data/*.toml, write README.md (entries marked `featured`) and full-list.md
(every entry), and build the bilingual GitHub Pages site (site/).

Usage: python3 scripts/build.py [--check | --site-only]   (standard library only, latest Python release)
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
STATUS = {"active", "slow", "inactive", "archived", "dead"}
REGIMES = {"activity", "work", "operating"}  # what keeps an entry current: recent activity, nothing (a finished work), being open
CONFIDENCE = {"high", "medium", "low"}
KINDS = {"official", "read", "indexed", "third-party", "forum"}
FUNDING = {"affiliation", "ads", "sponsorship", "subscription", "donations", "shop", "none", "unknown"}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ID = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

T = {  # interface strings
    "title": {"en": "Awesome LEGO", "fr": "Awesome LEGO"},
    "tagline": {"en": "Interlocking plastic construction bricks, from the official LEGO system to compatible brands.",
                "fr": "Briques de construction en plastique à emboîter, du système LEGO officiel aux marques compatibles."},
    "site_tagline": {"en": "The best of the brick world for adult builders, in official LEGO and compatible brands.",
                     "fr": "Le meilleur du monde de la brique pour les adultes qui construisent, en LEGO officiel comme en marques compatibles."},
    "feed": {"en": "Feed of new resources (RSS)", "fr": "Flux des nouveautés (RSS)"},
    "contents": {"en": "Contents", "fr": "Sommaire"},
    "contributing": {"en": "Contributing", "fr": "Contribuer"},
    "contrib_text": {"en": "Additions and corrections are welcome: read [contributing.md](contributing.md). Entries live in [`data/`](data/); this file is generated from them."},
    "site_fr": {"en": "French version of the website", "fr": "Version française du site"},
    "site": {"en": "Explore the website: every resource, with search, filters and a map", "fr": "Explorer le site : toutes les ressources, avec recherche, filtres et carte"},
    "updated": {"en": "Updated", "fr": "Mis à jour"},
    "resources": {"en": "resources", "fr": "ressources"},
}


def fail(errors):
    for e in errors:
        print("✗", e, file=sys.stderr)
    sys.exit(1)


def load():
    cats, errors, ids, urls = [], [], {}, {}
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
            if g.get("regime", "activity") not in REGIMES:
                errors.append(f"{where}: group {g['id']}: regime must be one of {sorted(REGIMES)}")
        for r in d.get("resource", []):
            w = f"{where}: {r.get('id', '?')}"
            if not ID.match(r.get("id", "")):
                errors.append(f"{w}: bad id")
            elif r["id"] in ids:
                errors.append(f"{w}: id already used in {ids[r['id']]}")
            ids[r.get("id")] = where
            for k in ("name", "url", "group", "summary_en", "summary_fr", "status", "checked", "added", "confidence"):
                if not r.get(k):
                    errors.append(f"{w}: {k} missing")
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
            if r.get("status") not in STATUS:
                errors.append(f"{w}: unknown status '{r.get('status')}'")
            if r.get("confidence") not in CONFIDENCE:
                errors.append(f"{w}: unknown confidence '{r.get('confidence')}'")
            for k in ("checked", "last_activity"):
                if r.get(k) and not DATE.match(str(r[k])):
                    errors.append(f"{w}: {k} must be YYYY-MM-DD")
            for a, b in (("strengths_en", "strengths_fr"), ("weaknesses_en", "weaknesses_fr")):
                if len(r.get(a, [])) != len(r.get(b, [])):
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
    return re.sub(r"[^a-z0-9 -]", "", s.lower().replace("’", "").replace("'", "")).strip().replace(" ", "-")


FILES = {("readme", "en"): "README.md", ("full", "en"): "full-list.md"}
MORE = {"readme": {"en": "Only the best of each group is listed here. The [full list](full-list.md) has every resource, including inactive and dead ones."},
        "full": {"en": "Every resource, including inactive and dead ones, generated from [`data/`](data/). The selection of the best is in the [README](README.md)."}}


def readme(cats, m, lang, kind="readme"):
    title = T["title"][lang] if kind == "readme" else "Awesome LEGO: full list"
    badge = " [![Awesome](https://awesome.re/badge.svg)](https://awesome.re)" if kind == "readme" else ""
    keep = (lambda r: r.get("featured")) if kind == "readme" else (lambda r: True)
    logo = [f'<a href="{PAGES}"><img src="media/logo.svg" align="right" width="120" alt="Awesome LEGO logo"></a>', ""] if kind == "readme" else []
    out = [f"# {title}{badge}", "", *logo, f"> {T['tagline'][lang]}", "",
           f"**[{T['site'][lang]}]({PAGES})** · [{T['site_fr'][lang]}]({PAGES}fr/) · [{T['feed'][lang]}]({PAGES}feed.xml)", "",
           *([f'<p align="center"><a href="{PAGES}"><img src="media/site-preview.png" width="880" alt="The website: the map of the brick world, one stud per resource by category, above the directory; tabs Directory, Out and about, Observatory"></a></p>', ""] if kind == "readme" else []),
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
    for c in cats:
        if not any(keep(r) for r in c["resources"]):
            continue
        name = c["category"][f"name_{lang}"]
        out.append(f"- [{name}](#{uniq(name)})")
        for g in c["category"].get("groups", []):
            if any(r["group"] == g["id"] and keep(r) for r in c["resources"]):
                out.append(f"  - [{g['name_' + lang]}](#{uniq(g['name_' + lang])})")
    listed = set()
    for c in cats:
        cat = c["category"]
        if not any(keep(r) for r in c["resources"]):
            continue
        # the icon floats left of the heading: inside the heading, awesome-lint and GitHub disagree on its anchor
        out += ["", "<br>", "", *([icon(cat["id"]), ""] if icon(cat["id"]) else []), f"## {cat['name_' + lang]}", ""]
        if cat.get("summary_" + lang):
            out += [cat["summary_" + lang], ""]
        for g in cat.get("groups", []):
            rs = [r for r in c["resources"] if r["group"] == g["id"] and keep(r) and (kind != "readme" or r["url"] not in listed)]
            listed.update(r["url"] for r in rs)  # the README gives a link once (awesome-lint: double-link); the full list gives every entry
            if not rs:
                continue
            out += [f"### {g['name_' + lang]}", ""]
            for r in sorted(rs, key=lambda r: r["name"].lower()):
                status = r["status"]  # declared status: generated files stay stable between data changes
                worlds = [w for k, w in (("official", "official LEGO"), ("alternative", "alternative brands")) if k in r.get("covers", [])]
                marks = (f"Covers {' and '.join(worlds)}." if worlds else "")
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


GEOFILE = DATA / "backend" / "geocode.json"
GEO = json.loads(GEOFILE.read_text(encoding="utf-8"))["places"] if GEOFILE.exists() else {}


def cities(r):
    """'Chambéry, Annecy' is two cities (same rule as scripts/geocode.py)."""
    return [c.strip() for c in str(r.get("city", "")).split(",") if c.strip()]


def geo_key(city, r):
    cc = [c for c in r.get("countries", []) if c != "international"]
    return f"{city}|{cc[0] if len(cc) == 1 else ''}"


def site_data(cats, m):
    rows = []
    for c in cats:
        cat = c["category"]
        gnames = {g["id"]: {"en": g["name_en"], "fr": g["name_fr"]} for g in cat.get("groups", [])}
        for r in c["resources"]:
            status, last = effective(r, m)
            row = {k: r.get(k) for k in ("id", "name", "url", "covers", "languages", "countries", "access", "confidence", "checked", "github", "subreddit", "featured", "city", "ships_to_france")}
            row["next"] = str(r["next_date"]) if r.get("next_date") and str(r["next_date"]) >= dt.date.today().isoformat() else None  # past dates are dropped at each daily build
            row.update(cat=cat["id"], group=r["group"], status=status, last=last, regime=r["_regime"],
                       metrics=m.get(r["id"], {}),
                       sources=[{"url": s["url"], "date": str(s["date"]), "kind": s["kind"]} for s in r.get("sources", [])])
            for lang in LANGS:
                row[lang] = {"summary": r["summary_" + lang], "strengths": r.get("strengths_" + lang, []),
                             "weaknesses": r.get("weaknesses_" + lang, []), "size": r.get("size_" + lang, ""),
                             "model": r.get("business_model_" + lang, ""), "group": gnames.get(r["group"], {}).get(lang, r["group"]),
                             **({"rec": r["recurrence_" + lang]} if r.get("recurrence_" + lang) else {})}
            row["checked"] = str(row["checked"])
            row["brands"] = r.get("brands", [])  # read at the source of each entry (brands of brands.toml it sells, tracks, reviews or admits)
            row["funding"] = r.get("funding")
            if r.get("contact"):
                row["contact"] = {k: r["contact"][k] for k in ("address", "phone", "email") if r["contact"].get(k)}
            if r.get("makers"):
                row["makers"] = [{k: str(x[k]) for k in ("name", "name_fr", "id", "url", "date", "kind") if x.get(k)} for x in r["makers"]]
            row["geo"] = [[GEO[k]["lat"], GEO[k]["lon"], c] for c in cities(r) for k in [geo_key(c, r)] if k in GEO]
            rows.append(row)
    categories = [{"id": c["category"]["id"], "en": c["category"]["name_en"], "fr": c["category"]["name_fr"],
                   "summary": {lang: c["category"].get("summary_" + lang, "") for lang in LANGS},
                   "groups": [{"id": g["id"], "en": g["name_en"], "fr": g["name_fr"]} for g in c["category"].get("groups", [])]} for c in cats]
    ids = {r["id"] for r in rows}
    journeys = tomllib.loads(pathlib.Path(DATA / "journeys.toml").read_text(encoding="utf-8")).get("journey", []) if (DATA / "journeys.toml").exists() else []
    missing = [f"journeys.toml: {j['id']}: unknown resource {i}" for j in journeys for i in j["resources"] + j.get("always", []) if i not in ids]
    missing += [f"journeys.toml: {j['id']}: scope must be country, language or global" for j in journeys if j.get("scope") not in ("country", "language", "global")]
    if missing:
        fail(missing)
    return {"built": dt.date.today().isoformat(), "categories": categories, "resources": rows, "journeys": journeys,
            "brands": alt_brands(cats), "passion": passion()}


def passion():
    """Recognized fan communities per country against population (backend data, not shown as entries)."""
    cf, pf = DATA / "backend" / "clubs-by-country.json", DATA / "backend" / "population.json"
    if not (cf.exists() and pf.exists()):
        return None
    c, p = json.loads(cf.read_text(encoding="utf-8")), json.loads(pf.read_text(encoding="utf-8"))
    return {"source": c["source"], "date": c["date"], "pop_source": p["source"], "pop_year": p["year"],
            "rows": [{"c": k, "n": n, "pop": p["population"].get(k)} for k, n in c["countries"].items()]}


def static_texts(tpl, lang):
    """Fill the empty elements marked data-t="key" with the string the page's script would put there
    (same table S of site-src/index.html): the first paint shows the final texts, nothing moves after."""
    S = {}
    for m in re.finditer(r"(?<![\w.])(\w+):\{en:'((?:[^'\\]|\\.)*)',fr:'((?:[^'\\]|\\.)*)'\}", tpl):
        S.setdefault(m.group(1), (m.group(2) if lang == "en" else m.group(3)).replace("\\'", "'"))
    return re.sub(r'(<(\w+)\b[^>]*\bdata-t="(\w+)"[^>]*>)(</\2>)',
                  lambda m: m.group(1) + html.escape(S[m.group(3)], quote=False) + m.group(4) if m.group(3) in S else m.group(0), tpl)


def page(lang, data):
    tpl = static_texts((ROOT / "site-src" / "index.html").read_text(encoding="utf-8"), lang)
    other = "fr/" if lang == "en" else "../"
    other_lang = "fr" if lang == "en" else "en"
    lean = dict(data, resources=[{k: v for k, v in r.items() if k != other_lang} for r in data["resources"]])  # each page carries its own language only
    blob = json.dumps(lean, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")  # no "</script" nor "<!--" inside the data block
    values = {"LANG": lang, "OTHER": other, "TITLE": html.escape(T["title"][lang]), "TAGLINE": html.escape(T["site_tagline"][lang]),
              "MINISEARCH": (ROOT / "site-src" / "vendor" / "minisearch.min.js").read_text(encoding="utf-8"),
              "FEEDTITLE": html.escape(FEED_T["title"][lang]), "FEEDPATH": "fr/" if lang == "fr" else "",
              "DATA": blob, "REPO": REPO, "VERSION": data["version"], "CSP": "{{CSP}}"}
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


def csp(doc, rest="; style-src 'unsafe-inline'; img-src 'self' https://actarus314.github.io; connect-src 'self' https://nominatim.openstreetmap.org; base-uri 'none'; form-action 'none'"):
    """Content security policy (GitHub Pages sends no headers: a meta element, placed before the first script).
    Only the page's own inline scripts run, each allowed by its hash; nothing is loaded from elsewhere."""
    hashes = [base64.b64encode(hashlib.sha256(m.encode("utf-8")).digest()).decode()
              for m in inline_scripts(doc)]
    return "default-src 'none'; script-src " + " ".join(f"'sha256-{h}'" for h in hashes) + rest


def vault():
    """The Brick Vault (site/vault/): an English-only easter egg that the Konami code opens from either home page.
    Its fonts are served by the site itself (media/fonts/, SIL Open Font License); it contacts nothing else."""
    doc = (ROOT / "site-src" / "vault.html").read_text(encoding="utf-8")
    return doc.replace("{{CSP}}", csp(doc, "; style-src 'unsafe-inline'; font-src 'self'; img-src 'self'; connect-src 'none'; base-uri 'none'; form-action 'none'"))


BASELINE = "2026-11-23"  # the directory's first day: its entries make one opening item, not 400 separate ones
FEED_T = {
    "title": {"en": "Awesome LEGO: new in the directory", "fr": "Awesome LEGO : nouveautés de l'annuaire"},
    "new": {"en": "New", "fr": "Nouveau"},
    "next": {"en": "Next edition", "fr": "Prochaine édition"},
    "open": {"en": "Awesome LEGO opens with {n} resources", "fr": "Awesome LEGO ouvre avec {n} ressources"},
    "open_body": {"en": "{n} resources of the brick world, each checked at its source: brands, shops, prices, second-hand, communities, videos, events, places, clubs, learning and tools.",
                  "fr": "{n} ressources du monde de la brique, chacune vérifiée à sa source : marques, boutiques, prix, occasion, communautés, vidéos, événements, lieux, clubs, savoir et outils."},
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


def content_feed(cats, lang):
    """What readers follow: entries added to the directory and announced editions of events, in one language."""
    site = PAGES + ("fr/" if lang == "fr" else "")
    today = dt.date.today().isoformat()
    items, base = [], 0
    for c in cats:
        cname = c["category"]["name_" + lang]
        for r in c["resources"]:
            link = f"{site}#entry={r['id']}"
            if str(r["added"]) <= BASELINE:
                base += 1
            else:
                items.append((f"{site}#added-{r['id']}", f"{FEED_T['new'][lang]} · {cname} · {r['name']}", link, str(r["added"]), r["summary_" + lang]))
            if r.get("next_date") and str(r["next_date"]) >= today:
                when = ".".join(reversed(str(r["next_date"]).split("-")))  # DD.MM.YYYY
                where = f" · {r['city']}" if r.get("city") else ""
                items.append((f"{site}#next-{r['id']}-{r['next_date']}", f"{FEED_T['next'][lang]} · {r['name']} · {when.replace('.', '/')}{where}",
                              link, str(r["checked"]), r["summary_" + lang]))
    if base:
        items.append((f"{site}#opening", FEED_T["open"][lang].format(n=base), site, BASELINE, FEED_T["open_body"][lang].format(n=base)))
    items.sort(key=lambda x: (x[3], x[1]), reverse=True)
    return atom(FEED_T["title"][lang], site + "feed.xml", site, items[:60])


COUNTRY = {  # names for the calendar (the website names countries in the visitor's language with Intl.DisplayNames)
    "AT": ("Austria", "Autriche"), "AU": ("Australia", "Australie"), "BE": ("Belgium", "Belgique"), "CA": ("Canada", "Canada"),
    "CH": ("Switzerland", "Suisse"), "CN": ("China", "Chine"), "CZ": ("Czechia", "Tchéquie"), "DE": ("Germany", "Allemagne"),
    "DK": ("Denmark", "Danemark"), "ES": ("Spain", "Espagne"), "FI": ("Finland", "Finlande"), "FR": ("France", "France"),
    "GB": ("United Kingdom", "Royaume-Uni"), "IE": ("Ireland", "Irlande"), "IT": ("Italy", "Italie"), "LU": ("Luxembourg", "Luxembourg"),
    "MC": ("Monaco", "Monaco"), "NL": ("Netherlands", "Pays-Bas"), "NO": ("Norway", "Norvège"), "NZ": ("New Zealand", "Nouvelle-Zélande"),
    "PL": ("Poland", "Pologne"), "PT": ("Portugal", "Portugal"), "SE": ("Sweden", "Suède"), "SK": ("Slovakia", "Slovaquie"),
    "US": ("United States", "États-Unis"), "ZA": ("South Africa", "Afrique du Sud")}


def calendar(cats, lang):
    """iCalendar file of the announced next editions (all-day events: only the start date is known)."""
    def esc(x):
        return str(x).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

    def fold(line):  # RFC 5545: lines of at most 75 octets, continued with a space
        out, cur = [], ""
        for ch in line:
            if len((cur + ch).encode("utf-8")) > 75:
                out.append(cur)
                cur = " " + ch
            else:
                cur += ch
        return "\r\n".join(out + [cur])
    today = dt.date.today()
    stamp = today.strftime("%Y%m%dT000000Z")
    site = PAGES + ("fr/" if lang == "fr" else "")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//actarus314//Awesome LEGO//" + lang.upper(), "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
             "X-WR-CALNAME:" + esc(CAL_T[lang]), "REFRESH-INTERVAL;VALUE=DURATION:P1D", "X-PUBLISHED-TTL:P1D"]  # subscribed calendars come back once a day (RFC 7986)
    for c in cats:
        for r in c["resources"]:
            nd = str(r.get("next_date") or "")
            if not nd or nd < today.isoformat():
                continue
            d = dt.date.fromisoformat(nd)
            cc = [x for x in r.get("countries", []) if x in COUNTRY]
            where = ", ".join(filter(None, [r.get("city", ""), COUNTRY[cc[0]][LANGS.index(lang)] if len(cc) == 1 else ""]))
            lines += ["BEGIN:VEVENT", f"UID:{r['id']}-{nd}@actarus314.github.io", "DTSTAMP:" + stamp,
                      "DTSTART;VALUE=DATE:" + d.strftime("%Y%m%d"), "DTEND;VALUE=DATE:" + (d + dt.timedelta(days=1)).strftime("%Y%m%d"),
                      "SUMMARY:" + esc(r["name"]), *(["LOCATION:" + esc(where)] if where else []),
                      "DESCRIPTION:" + esc(r["summary_" + lang] + (" " + r["recurrence_" + lang] + "." if r.get("recurrence_" + lang) else "") + " " + CAL_T["dates"][lang]),
                      "URL:" + r["url"], "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(fold(l) for l in lines) + "\r\n"


CAL_T = {"en": "Awesome LEGO: next editions", "fr": "Awesome LEGO : prochaines éditions",
         "dates": {"en": "Start date as announced; check the dates and opening hours on the event's site.",
                   "fr": "Date de début annoncée ; vérifier les dates et horaires sur le site de l'événement."}}


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


def check_docs():
    """The documents that describe the data and the automation must name what exists."""
    errors = []
    schema = (DATA / "SCHEMA.md").read_text(encoding="utf-8")
    for name, words in (("covers", COVERS), ("access", ACCESS), ("status", STATUS), ("regime", REGIMES), ("kind", KINDS), ("funding", FUNDING)):
        line = next((l for l in schema.splitlines() if l.startswith(f"{name} = ")), "")
        missing = sorted(w for w in words if not re.search(rf"\b{re.escape(w)}\b", line))
        if missing:
            errors.append(f"data/SCHEMA.md: the `{name}` line does not list {', '.join(missing)}")
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


def main():
    cats, errors = load()
    errors += check_docs()
    if errors:
        fail(errors)
    m = metrics()
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not re.search(rf"^## v{re.escape(version)} — \d{{4}}-\d{{2}}-\d{{2}}$", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), re.M):
        fail([f"CHANGELOG.md has no '## v{version} — YYYY-MM-DD' section for VERSION {version}"])
    missing = sorted({geo_key(c, r) for cat in cats for r in cat["resources"] for c in cities(r)} - set(GEO))
    for k in missing:
        print(f"! no coordinates for {k}: run python3 scripts/geocode.py (the entry stays off the map)")
    texts = {f: readme(cats, m, lang, kind) for (kind, lang), f in FILES.items()}
    texts[".github/ISSUE_TEMPLATE/add-resource.yml"] = issue_form(cats)
    print(f"✓ v{version}: {sum(len(c['resources']) for c in cats)} resources in {len(cats)} categories")
    if "--check" in sys.argv:
        stale = [f for f, t in texts.items() if not (ROOT / f).exists() or (ROOT / f).read_text(encoding="utf-8") != t]
        if stale:
            fail([f"{f} is out of date: run python3 scripts/build.py and commit it" for f in stale])
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
    (SITE / "vault").mkdir(parents=True, exist_ok=True)
    (SITE / "vault" / "index.html").write_text(vault(), encoding="utf-8")
    (SITE / "feed.xml").write_text(content_feed(cats, "en"), encoding="utf-8")
    (SITE / "fr" / "feed.xml").write_text(content_feed(cats, "fr"), encoding="utf-8")
    (SITE / "changes.xml").write_text(changes_feed(), encoding="utf-8")
    (SITE / "agenda.ics").write_text(calendar(cats, "en"), encoding="utf-8", newline="")
    (SITE / "fr" / "agenda.ics").write_text(calendar(cats, "fr"), encoding="utf-8", newline="")
    (SITE / "favicon.ico").write_bytes((ROOT / "media" / "favicon.ico").read_bytes())  # readers that look for <site>/favicon.ico
    for f in (ROOT / "media").rglob("*"):
        if f.is_file() and f.name != "site-preview.png":  # the README image is read on GitHub, not on the website
            out = SITE / f.relative_to(ROOT)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(f.read_bytes())
    (SITE / "data.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")  # read by scripts/refresh.py --from-site
    print("✓ site/index.html, site/fr/index.html, site/data.json")


if __name__ == "__main__":
    main()
