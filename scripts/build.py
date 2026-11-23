#!/usr/bin/env python3
"""Validate data/*.toml, write README.md (entries marked `featured`) and full-list.md
(every entry), and build the bilingual GitHub Pages site (site/).

Usage: python3 scripts/build.py [--check | --site-only]   (standard library only, Python 3.11+)
"""
import datetime as dt
import html
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
ORDER = ["brands", "shops", "comparators", "second-hand", "community", "video", "tools", "directories"]
COVERS = {"official", "alternative", "second-hand", "parts", "custom-builds", "minifigures", "instructions", "news", "data"}
ACCESS = {"free", "free-account", "freemium", "paid"}
STATUS = {"active", "slow", "inactive", "archived", "dead"}
CONFIDENCE = {"high", "medium", "low"}
KINDS = {"official", "read", "indexed", "third-party", "forum"}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ID = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

T = {  # interface strings
    "title": {"en": "Awesome LEGO", "fr": "Awesome LEGO"},
    "tagline": {"en": "Interlocking plastic construction bricks, from the official LEGO system to compatible brands.",
                "fr": "Briques de construction en plastique à emboîter, du système LEGO officiel aux marques compatibles."},
    "site_tagline": {"en": "Brands, shops, price comparators, second-hand, communities, videos and tools for adult builders of official LEGO and compatible bricks.",
                     "fr": "Marques, boutiques, comparateurs, occasion, communautés, vidéos et outils pour les adultes qui construisent en LEGO officiel et en briques compatibles."},
    "contents": {"en": "Contents", "fr": "Sommaire"},
    "contributing": {"en": "Contributing", "fr": "Contribuer"},
    "contrib_text": {"en": "Additions and corrections are welcome: read [contributing.md](contributing.md). Entries live in [`data/`](data/); this file is generated from them."},
    "site_fr": {"en": "French version of the website", "fr": "Version française du site"},
    "site": {"en": "Website with search, filters and charts", "fr": "Site avec recherche, filtres et graphiques"},
    "updated": {"en": "Updated", "fr": "Mis à jour"},
    "resources": {"en": "resources", "fr": "ressources"},
}


def fail(errors):
    for e in errors:
        print("✗", e, file=sys.stderr)
    sys.exit(1)


def load():
    cats, errors, ids = [], [], {}
    for path in sorted(DATA.glob("*.toml")):
        if path.stem == "metrics":
            continue
        try:
            d = tomllib.load(open(path, "rb"))
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
        for r in d.get("resource", []):
            w = f"{where}: {r.get('id', '?')}"
            if not ID.match(r.get("id", "")):
                errors.append(f"{w}: bad id")
            elif r["id"] in ids:
                errors.append(f"{w}: id already used in {ids[r['id']]}")
            ids[r.get("id")] = where
            for k in ("name", "url", "group", "summary_en", "summary_fr", "status", "checked", "confidence"):
                if not r.get(k):
                    errors.append(f"{w}: {k} missing")
            if not re.match(r"https?://", str(r.get("url", ""))):
                errors.append(f"{w}: url must start with https:// or http://")
            if r.get("group") not in groups:
                errors.append(f"{w}: group '{r.get('group')}' not in category.groups")
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
        cats.append({"category": c, "resources": d.get("resource", [])})
    cats.sort(key=lambda x: ORDER.index(x["category"]["id"]) if x["category"].get("id") in ORDER else 99)
    return cats, errors


def metrics():
    p = DATA / "metrics.json"
    return json.load(open(p, encoding="utf-8")) if p.exists() else {}


def effective(r, m):
    """Status and last activity, after automatic metrics (data/metrics.json)."""
    last = str(r.get("last_activity") or "")
    auto = m.get(r["id"], {}).get("last_activity")
    if auto and auto > last:
        last = auto
    status = r["status"]
    if status in ("active", "slow", "inactive") and last:
        days = (dt.date.today() - dt.date.fromisoformat(last)).days
        status = "active" if days <= 183 else "slow" if days <= 365 else "inactive"
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
    out = [f"# {title}{badge}", "", f"> {T['tagline'][lang]}", "",
           f"[{T['site'][lang]}]({PAGES}) · [{T['site_fr'][lang]}]({PAGES}fr/)", "",
           MORE[kind][lang], "", f"## {T['contents'][lang]}", ""]
    seen = {}

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
        out += ["", f"## {cat['name_' + lang]}", ""]
        if cat.get("summary_" + lang):
            out += [cat["summary_" + lang], ""]
        for g in cat.get("groups", []):
            rs = [r for r in c["resources"] if r["group"] == g["id"] and keep(r) and r["url"] not in listed]
            listed.update(r["url"] for r in rs)  # one link once per file (awesome-lint: double-link)
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
                if not desc.endswith("."):
                    desc += "."
                out.append(f"- [{r['name']}]({r['url']}) - {desc}{(' ' + marks.strip()) if marks.strip() else ''}")
            out.append("")
    out += [f"## {T['contributing'][lang]}", "", T["contrib_text"][lang], ""]
    return "\n".join(out).replace("\n\n\n", "\n\n")


def site_data(cats, m):
    rows = []
    for c in cats:
        cat = c["category"]
        gnames = {g["id"]: {"en": g["name_en"], "fr": g["name_fr"]} for g in cat.get("groups", [])}
        for r in c["resources"]:
            status, last = effective(r, m)
            row = {k: r.get(k) for k in ("id", "name", "url", "covers", "languages", "countries", "access", "confidence", "checked", "github", "subreddit", "featured")}
            row.update(cat=cat["id"], group=r["group"], status=status, last=last,
                       metrics=m.get(r["id"], {}),
                       sources=[{"url": s["url"], "date": str(s["date"]), "kind": s["kind"]} for s in r.get("sources", [])])
            for lang in LANGS:
                row[lang] = {"summary": r["summary_" + lang], "strengths": r.get("strengths_" + lang, []),
                             "weaknesses": r.get("weaknesses_" + lang, []), "size": r.get("size_" + lang, ""),
                             "model": r.get("business_model_" + lang, ""), "group": gnames.get(r["group"], {}).get(lang, r["group"])}
            row["checked"] = str(row["checked"])
            rows.append(row)
    categories = [{"id": c["category"]["id"], "en": c["category"]["name_en"], "fr": c["category"]["name_fr"],
                   "summary": {lang: c["category"].get("summary_" + lang, "") for lang in LANGS},
                   "groups": [{"id": g["id"], "en": g["name_en"], "fr": g["name_fr"]} for g in c["category"].get("groups", [])]} for c in cats]
    return {"built": dt.date.today().isoformat(), "categories": categories, "resources": rows}


def page(lang, data):
    tpl = (ROOT / "site-src" / "index.html").read_text(encoding="utf-8")
    other = "fr/" if lang == "en" else "../"
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return (tpl.replace("{{LANG}}", lang).replace("{{OTHER}}", other)
               .replace("{{TITLE}}", html.escape(T["title"][lang])).replace("{{TAGLINE}}", html.escape(T["site_tagline"][lang]))
               .replace("{{DATA}}", blob).replace("{{REPO}}", REPO).replace("{{VERSION}}", data["version"]))


def main():
    cats, errors = load()
    if errors:
        fail(errors)
    m = metrics()
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not re.search(rf"^## v{re.escape(version)} — \d{{4}}-\d{{2}}-\d{{2}}$", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), re.M):
        fail([f"CHANGELOG.md has no '## v{version} — YYYY-MM-DD' section for VERSION {version}"])
    texts = {f: readme(cats, m, lang, kind) for (kind, lang), f in FILES.items()}
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
    (SITE / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("✓ site/index.html, site/fr/index.html, site/data.json")


if __name__ == "__main__":
    main()
