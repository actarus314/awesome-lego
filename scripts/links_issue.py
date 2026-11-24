#!/usr/bin/env python3
"""Body of the "Broken links" issue (standard library only).

Three readings, from three places:
1. lychee, from the machines of GitHub (its Markdown report is the input): every link of the data and the documents.
2. Globalping (https://globalping.io, free public API of jsDelivr): every link that failed from GitHub is opened
   again from 3 probes, on home and office networks when there are enough ("eyeball" probes: 2 in Europe, 1 in
   North America). A link that fails from every probe is broken. A link that answers somewhere blocks the machines
   of GitHub and is alive: it goes to a short list, never to the broken links. Redirects count as alive (Data fixes
   replaces addresses that moved for good). Token: GLOBALPING_TOKEN, optional (higher hourly limit).
3. The address of every entry, opened from GitHub: a page that answers 200 but is dead (parked domain, closure
   notice, site taken over by unrelated content) is listed too.
Without Globalping (limit reached, service down), the failures keep the old order: failed twice in a row first.

Usage:
  links_issue.py REPORT [PREVIOUS_BODY] [--recheck] [--pages] [--state FILE] > body.md
      REPORT: lychee report (a missing or empty file means no failure); PREVIOUS_BODY: the issue's last body.
      --state FILE: writes "open" when something needs a person, else "close".
  links_issue.py --sample tests/links-sample.json
      reads the real addresses of the sample and compares each verdict with the expected one (exit 1 on a mismatch).
"""
import concurrent.futures
import datetime as dt
import html
import json
import os
import pathlib
import re
import sys
import time
import tomllib
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
LINE = re.compile(r"^\* \[[^\]]+\] <(?P<url>[^>]+)> \(at (?P<at>\d+:\d+)\) \| (?P<why>.*)$")
FILE = re.compile(r"^### (?:Errors|Timeouts) in (?P<file>\S+)")
LIMIT = 60000   # an issue body holds 65536 characters at most
UA = "awesome-lego-links/1.0 (+https://github.com/actarus314/awesome-lego)"
API = "https://api.globalping.io/v1"
ACCEPT = {401, 403, 405, 429}   # as lychee in links.yml: a bot check, another method, a rate limit
PROBES = [{"magic": "europe+eyeball", "limit": 2}, {"magic": "north america+eyeball", "limit": 1}]
FALLBACK = [{"magic": "world", "limit": 3}]   # when too few eyeball probes are online
PER_URL = 3   # tests of Globalping per link
PLATFORMS = ("youtube.com", "reddit.com", "github.com", "facebook.com", "instagram.com", "discord.gg", "discord.com",
             "x.com", "twitter.com", "tiktok.com", "flickr.com", "patreon.com", "twitch.tv")   # their pages never park

# Dead pages that answer 200. Each pattern is matched case-insensitively.
PARKED = [  # parking services, domain marketplaces, expired or suspended hosting
    r"sedoparking\.com", r"parkingcrew\.net", r"bodis\.com", r"above\.com/marketplace", r"\bdan\.com/", r"afternic\.com",
    r"hugedomains\.com", r"undeveloped\.com", r"nameshift\.com", r"domainmarket\.com", r"parklogic", r"/lander\b",
    r"this domain (is|may be) for sale", r"buy this domain", r"domain (is )?parked", r"parked free",
    r"le nom de domaine [^<]{0,80} est à vendre", r"ce (nom de )?domaine est à vendre", r"diese domain (steht zum verkauf|kaufen|ist zu verkaufen)",
    r"questo dominio è in vendita", r"este dominio (está a la venta|se vende)", r"deze domeinnaam is te koop",
    r"this domain (name )?has expired", r"domain (name )?has expired", r"account (has been )?suspended", r"website expired"]
CLOSED = [  # closure notices, looked for in the title, headings, description and the start of the text
    r"permanently closed", r"closed permanently", r"closed for good", r"has closed (down|its doors)", r"we have (now )?closed",
    r"(is|are) no longer (trading|operating|in business)", r"ceased trading", r"shut down (permanently|for good)",
    r"(site|website|shop|store) (has been|is) (closed|discontinued|shut down)",
    r"définitivement fermée?s?", r"a fermé (ses portes|définitivement)", r"fermeture définitive", r"nous avons fermé", r"cessation d'activité",
    r"dauerhaft geschlossen", r"endgültig geschlossen", r"wir haben (unseren shop |unser geschäft )?geschlossen", r"geschäftsaufgabe",
    r"chiuso definitivamente", r"chiusura definitiva", r"cessata attività",
    r"cerrado (definitivamente|permanentemente)", r"cierre definitivo",
    r"definitief gesloten", r"permanent gesloten", r"lukket permanent", r"stängt permanent"]
TAKEN = [  # unrelated content in the title, the description or the main heading: the domain changed hands
    r"\bcasinos?\b", r"\bgambling\b", r"\bbetting\b", r"\bsportsbook\b", r"\bbookmakers?\b", r"\bpoker\b", r"\broulette\b",
    r"\bblackjack\b", r"\bslot gacor\b", r"\btogel\b", r"\bjudi\b", r"\bporn", r"\bxxx\b", r"\bviagra\b", r"\bcialis\b",
    r"\bescorts?\b", r"\bpayday loans?\b"]


def date_en(d):
    return f"{d.day} {d:%B} {d.year}"


def failures(text):
    """{url: (file, position, reason)} for each failing link, first place only."""
    out, file = {}, "?"
    for line in text.splitlines():
        if m := FILE.match(line):
            file = m["file"]
        elif m := LINE.match(line):
            out.setdefault(m["url"], (file, m["at"], m["why"]))
    return out


# --- Globalping -----------------------------------------------------------------------------------------------

def _api(path, body=None, token=None):
    h = {"User-Agent": UA, "Accept": "application/json", "Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(API + path, data=json.dumps(body).encode() if body is not None else None, headers=h)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def _request(url):
    u = urllib.parse.urlsplit(url)
    req = {"method": "GET", "path": u.path or "/"}   # GET: the first 10 kB of the page are judged too (classify)
    if u.query:
        req["query"] = u.query
    opts = {"protocol": "HTTP" if u.scheme == "http" else "HTTPS", "request": req}
    if u.port:
        opts["port"] = u.port
    return {"type": "http", "target": u.hostname, "measurementOptions": opts}


def reason(result):
    """Short reason of one probe's answer."""
    if result.get("status") == "finished":
        return str(result.get("statusCode"))
    raw = (result.get("rawOutput") or "").lower()
    for key, text in (("enotfound", "name not found"), ("eai_again", "name not found"), ("timed out", "timed out"),
                      ("etimedout", "timed out"), ("econnrefused", "connection refused"), ("enetunreach", "unreachable"),
                      ("ehostunreach", "unreachable"), ("econnreset", "connection reset"), ("certificate", "certificate error"),
                      ("tls", "TLS error"), ("ssl", "TLS error")):
        if key in raw:
            return text
    return raw.strip().splitlines()[0][:60] if raw.strip() else result.get("status", "?")


def alive(result):
    code = result.get("statusCode") if result.get("status") == "finished" else None
    return code is not None and (200 <= code < 400 or code in ACCEPT)


def verdict(results):
    """("alive" | "down" | "unchecked", reasons of the probes, (kind, evidence) of a dead page or None)."""
    rs = [r.get("result", {}) for r in results if r.get("result", {}).get("status") in ("finished", "failed")]
    if not rs:
        return "unchecked", [], None
    found = next((f for r in rs if r.get("statusCode") == 200 and r.get("rawBody") for f in [classify(r["rawBody"])] if f), None)
    return ("alive" if any(alive(r) for r in rs) else "down"), [reason(r) for r in rs], found


def recheck(urls, token=None, api=_api, sleep=time.sleep):
    """{url: (verdict, reasons, dead page)} from Globalping; links over the hourly limit are left out (unchecked)."""
    try:
        left = api("/limits", token=token)["rateLimit"]["measurements"]["create"]["remaining"]
    except Exception:
        left = 0
    out, ids = {}, {}
    for url in urls[: max(0, left) // PER_URL]:
        for locations in (PROBES, FALLBACK):
            try:
                ids[url] = api("/measurements", dict(_request(url), locations=locations), token)["id"]
                break
            except urllib.error.HTTPError as e:
                if e.code != 422:   # 422: no suitable probes for these locations
                    break
            except Exception:
                break
    for url, i in ids.items():
        for _ in range(60):
            try:
                m = api(f"/measurements/{i}", token=token)
            except Exception:
                break
            if m.get("status") != "in-progress":
                out[url] = verdict(m.get("results", []))
                break
            sleep(0.6)   # the API asks for 500 ms between two reads of one measurement
    return out


# --- Dead pages that answer 200 ---------------------------------------------------------------------------------

def _text(page):
    """(title, description, headings, start of the visible text) of an HTML page."""
    t = re.search(r"<title[^>]*>(.*?)</title>", page, re.S | re.I)
    d = re.search(r"<meta[^>]+(?:name|property)=[\"'](?:og:)?description[\"'][^>]*content=[\"']([^\"']*)", page, re.I)
    heads = " ".join(re.findall(r"<h[12][^>]*>(.*?)</h[12]>", page, re.S | re.I))
    body = re.sub(r"<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", page, flags=re.S | re.I)
    clean = lambda s: html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or ""))).strip()
    return clean(t.group(1) if t else ""), clean(d.group(1) if d else ""), clean(heads), clean(body)[:3000]


def classify(page):
    """(kind, evidence) for a dead page, else None. Kinds: parked or expired, taken over, closed."""
    title, desc, heads, start = _text(page)
    for p in PARKED:
        if m := re.search(p, page, re.I):
            return "parked or expired", m.group(0)
    for p in TAKEN:
        if m := re.search(p, f"{title} | {desc} | {heads}", re.I):
            return "taken over", f"{m.group(0)}: “{(title or desc)[:90]}”"
    for p in CLOSED:
        if m := re.search(p, f"{title} | {desc} | {heads} | {start}", re.I):
            return "closed", m.group(0)
    return None


def _fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*;q=0.5"})
    with urllib.request.urlopen(req, timeout=20) as r:
        if r.status != 200 or "html" not in r.headers.get("Content-Type", "html"):
            return None
        raw = r.read(400_000)
        return raw.decode(r.headers.get_content_charset() or "utf-8", "replace")


def entries():
    """[(id, url)] of every entry, platforms left out."""
    out = []
    for path in sorted((ROOT / "data").glob("*.toml")):
        for r in tomllib.loads(path.read_text(encoding="utf-8")).get("resource", []):
            host = (urllib.parse.urlsplit(r["url"]).hostname or "").removeprefix("www.")
            if not any(host == p or host.endswith("." + p) for p in PLATFORMS):
                out.append((r["id"], r["url"]))
    return out


def dead_pages(items, fetch=_fetch):
    """[(url, "entry `id`", kind, evidence)] of the pages that answer 200 but are dead; a page that fails is lychee's."""
    def one(item):
        try:
            page = fetch(item[1])
        except Exception:
            return None
        found = classify(page) if page else None
        return (item[1], f"entry `{item[0]}`", *found) if found else None
    with concurrent.futures.ThreadPoolExecutor(12) as pool:
        return sorted(x for x in pool.map(one, items) if x)


# --- Issue body -------------------------------------------------------------------------------------------------

def body(report, previous="", rechecked=None, dead=(), today=None):
    """(text, needs_a_person). rechecked=None: Globalping was not asked."""
    today = today or dt.date.today()
    now = failures(report)
    before = set(re.findall(r"<(https?://[^>]+)>", previous))
    rechecked = rechecked if rechecked is not None else {}
    at = lambda u: f"{now[u][0]} {now[u][1]}"
    broken = [u for u in now if rechecked.get(u, ("",))[0] == "down"]
    alive_dead = [(u, at(u), *rechecked[u][2]) for u in now if rechecked.get(u, ("",))[0] == "alive" and rechecked[u][2]]
    blocked = [u for u in now if rechecked.get(u, ("",))[0] == "alive" and not rechecked[u][2]]
    dead = sorted(set(dead) | {x for x in alive_dead if x[0] not in {d[0] for d in dead}})   # read by Globalping when GitHub could not
    unchecked = [u for u in now if rechecked.get(u, ("",))[0] not in ("down", "alive")]
    order = lambda us: sorted(us, key=lambda u: now[u][:2])
    gp = lambda u: ", ".join(rechecked[u][1])
    again = lambda u: " | also last week" if u in before else ""
    out = [f"{len(now)} links failed from the machines of GitHub on {date_en(today)}"
           + (f"; {len(now) - len(unchecked)} were opened again from 3 probes of Globalping, on home and office networks."
              if len(now) - len(unchecked) else "."), ""]
    if broken:
        out += ["## Broken: they fail from GitHub and from every probe", ""]
        out += [f"* <{u}> ({at(u)}) | GitHub: {now[u][2]} | Globalping: {gp(u)}{again(u)}" for u in order(broken)] + [""]
    if dead:
        out += ["## They answer, but the page is dead", ""]
        out += [f"* <{u}> ({where}) | {kind}: {ev}{again(u)}" for u, where, kind, ev in dead] + [""]
    if unchecked:
        twice = [u for u in unchecked if u in before]
        once = [u for u in unchecked if u not in before]
        out += ["## Not opened again (Globalping unavailable or over its hourly limit)", "",
                "Some sites refuse the machines of GitHub but open in a browser: open a link before changing its entry.", ""]
        for title, urls in (("Failed twice in a row", twice), ("Failed in this run only", once)):
            if urls:
                out += [f"### {title}", ""] + [f"* <{u}> ({at(u)}) | {now[u][2]}" for u in order(urls)] + [""]
    if blocked:
        out += [f"<details><summary>They block GitHub, alive according to Globalping on {date_en(today)} ({len(blocked)})</summary>", ""]
        out += [f"* <{u}> ({at(u)}) | GitHub: {now[u][2]} | Globalping: {gp(u)}" for u in order(blocked)] + ["", "</details>", ""]
    if not now and not dead:
        out = [f"Every link answers ({date_en(today)}).", ""]
    text = "\n".join(out)
    text = text if len(text) <= LIMIT else text[:LIMIT].rsplit("\n", 1)[0] + "\n\n(cut: too long for an issue)\n"
    return text, bool(broken or dead or unchecked)


# --- Sample: the yardstick of the checks, read live --------------------------------------------------------------

def sample(path, token=None):
    """Reads each address of the sample and compares the verdict with the expected one."""
    cases = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))["cases"]
    down = recheck([c["url"] for c in cases if c["check"] == "globalping"], token)
    pages = {u: (k, e) for u, _, k, e in dead_pages([(c["url"], c["url"]) for c in cases if c["check"] == "page"])}
    bad = 0
    for c in cases:
        got = down.get(c["url"], ("unchecked", []))[0] if c["check"] == "globalping" else pages.get(c["url"], ("healthy",))[0]
        ok = got == c["expected"]
        bad += not ok
        print(f"{'ok ' if ok else 'BAD'} {c['url']}: {got} (expected {c['expected']})"
              + (f" {down[c['url']][1]}" if c["url"] in down else f" {pages[c['url']][1]}" if c["url"] in pages else ""))
    print(f"{len(cases) - bad}/{len(cases)} as expected")
    return 1 if bad else 0


def main(argv):
    token = os.environ.get("GLOBALPING_TOKEN") or None
    if argv[:1] == ["--sample"]:
        return sample(argv[1], token)
    args = [a for a in argv if not a.startswith("--")]
    state = argv[argv.index("--state") + 1] if "--state" in argv else None
    if state in args:
        args.remove(state)
    report = pathlib.Path(args[0]).read_text(encoding="utf-8") if args and pathlib.Path(args[0]).exists() else ""
    previous = pathlib.Path(args[1]).read_text(encoding="utf-8") if len(args) > 1 and pathlib.Path(args[1]).exists() else ""
    rechecked = recheck(list(failures(report)), token) if "--recheck" in argv else None
    dead = dead_pages(entries()) if "--pages" in argv else ()
    text, needed = body(report, previous, rechecked, dead)
    if state:
        pathlib.Path(state).write_text("open" if needed else "close", encoding="utf-8")
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
