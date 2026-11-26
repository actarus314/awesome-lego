#!/usr/bin/env python3
"""Body of the "Broken links" issue (standard library only).

Three readings, from three places:
1. lychee, from the machines of GitHub (its Markdown report is the input): every link of the data and the documents.
2. Globalping (https://globalping.io, free public API of jsDelivr): every link that failed from GitHub is opened
   again from 3 probes on home and office networks ("eyeball" probes: 2 in Europe and 1 in North America, else any 3
   eyeball probes; never data centre probes, which fail like GitHub). A link that fails from every probe (2 readings at
   least) is broken. A link that answers somewhere blocks the machines of GitHub and is alive: it goes to a folded list,
   never to the broken links. A redirect is followed (3 hops at most): the link is judged by where it leads, and an
   address that moved for good is left to Data fixes. A link whose secure connection every probe refuses goes to a
   second folded list (browsers often still open it); a failure of the probe itself is not counted. When the hourly
   limit cuts the list, the links that failed in the previous run go first, then a different part of the others each
   week. A link found broken is read again 90 seconds later and stays broken only if it fails again; when it cannot
   be read a second time, it is not judged.
   Token: GLOBALPING_TOKEN, optional (higher hourly limit).
3. The address of every entry still open, opened from GitHub: a page that answers 200 but is dead (parked or expired
   domain, closure notice, site taken over by unrelated content) is listed too.
Text read on a third-party page or probe is quoted as code, so that it can neither mention nor link anyone.

Usage:
  links_issue.py REPORT [PREVIOUS_BODY] [--recheck] [--pages] [--state FILE] > body.md
      REPORT: lychee report (a missing or empty file means no failure); PREVIOUS_BODY: the issue's last body.
      --state FILE: writes "open" when something needs a person, else "close".
  links_issue.py --sample tests/links-sample.json
      reads the real addresses of the sample and compares each verdict with the expected one (exit 1 on a mismatch).
"""
import concurrent.futures
import datetime as dt
import hashlib
import html.parser
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

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from refresh import date_en  # noqa: E402  (one way of writing a date)

ROOT = pathlib.Path(__file__).resolve().parent.parent
LINE = re.compile(r"^\* \[[^\]]+\] <(?P<url>[^>]+)> \(at (?P<at>\d+:\d+)\) \| (?P<why>.*)$")
FILE = re.compile(r"^### (?:Errors|Timeouts) in (?P<file>\S+)")
LIMIT = 60000   # an issue body holds 65536 characters at most
UA = "awesome-lego-links/1.0 (+https://github.com/actarus314/awesome-lego)"
API = "https://api.globalping.io/v1"
ACCEPT = {401, 403, 405, 429}   # as lychee in links.yml: a bot check, another method, a rate limit
PROBES = [{"magic": "europe+eyeball", "limit": 2}, {"magic": "north america+eyeball", "limit": 1}]
FALLBACK = [{"magic": "eyeball", "limit": 3}]   # when too few eyeball probes are online in those regions
PER_URL = 3   # tests of Globalping per measurement
MIN_READINGS = 2   # a link is broken only if at least 2 probes really read it
HOPS = 3   # redirects followed
CONFIRM_PAUSE = 90   # seconds before a link that failed from every probe is read a second time
PLATFORMS = ("youtube.com", "reddit.com", "github.com", "facebook.com", "instagram.com", "discord.gg", "discord.com",
             "x.com", "twitter.com", "tiktok.com", "flickr.com", "patreon.com", "twitch.tv")   # their pages never park

# Dead pages that answer 200. Each pattern is matched case-insensitively.
PARKED_SITE = [  # in the HTML: a parking service or a domain marketplace that serves the page
    r"\bsedoparking\.com", r"\bparkingcrew\.net", r"\bbodis\.com", r"\bafternic\.com", r"\bhugedomains\.com",
    r"\bundeveloped\.com", r"\bnameshift\.com", r"\bdomainmarket\.com", r"\bparklogic\.com",
    r"location\.href\s*=\s*[\"']/lander[\"']"]
PARKED_TEXT = [  # in the title, the description and the main headings
    r"this domain (is|may be) for sale", r"buy this domain", r"this domain is parked", r"parked free, courtesy of",
    r"le nom de domaine \S+ est à vendre", r"ce (nom de )?domaine est à vendre", r"diese domain (steht zum verkauf|kaufen|ist zu verkaufen)",
    r"questo dominio è in vendita", r"este dominio (está a la venta|se vende)", r"deze domeinnaam is te koop",
    r"this domain (name )?has expired", r"website expired", r"this account has been suspended"]
CLOSED = [  # closure notices, in the title, headings, description and the start of the text
    r"permanently closed", r"closed permanently", r"closed for good", r"has closed (down|its doors)", r"we have (now )?closed (for good|permanently|our (shop|store|doors|business))",
    r"(is|are) no longer (trading|operating|in business)", r"ceased trading", r"shut down (permanently|for good)",
    r"(site|website|shop|store) (has been|is) (closed|discontinued|shut down)",
    r"définitivement fermée?s?", r"a fermé (ses portes|définitivement)", r"fermeture définitive", r"nous avons fermé", r"cessation d'activité",
    r"dauerhaft geschlossen", r"endgültig geschlossen", r"wir haben (unseren shop |unser geschäft )?geschlossen", r"geschäftsaufgabe",
    r"chiuso definitivamente", r"chiusura definitiva", r"cessata attività",
    r"cerrado (definitivamente|permanentemente)", r"cierre definitivo",
    r"definitief gesloten", r"permanent gesloten", r"lukket permanent", r"stängt permanent"]
TAKEN = [  # words of an unrelated trade in the title, the description or the main headings
    r"\bcasinos?\b", r"\bgambling\b", r"\bbetting\b", r"\bsportsbook\b", r"\bbookmakers?\b", r"\bpoker\b", r"\broulette\b",
    r"\bblackjack\b", r"\bslot gacor\b", r"\btogel\b", r"\b(situs|judi) (judi|online|slot)\b", r"\bporn", r"\bxxx\b",
    r"\bviagra\b", r"\bcialis\b", r"\bescorts?\b", r"\bpayday loans?\b"]
# ... and none of the words of the bricks there: a brick model of a casino or of a Ford Escort is no take-over
BRICKS = re.compile(r"lego|brick|briq|baustein|klemmbau|mattonc|ladrill|klock|kostk|kock|minifig|\bmoc\b|afol|\blug\b|technic|duplo", re.I)


_BRANDS = []   # filled on first use by brand_words()


def code(text):
    """Third-party text as a code span: no mention, link or issue reference can come alive in the issue."""
    t = re.sub(r"\s+", " ", str(text)).replace("`", "'").strip()
    return f"`{t}`" if t else "``"


def plural(n, one, many):
    return f"{n} {one if n == 1 else many}"


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
    raw = (result.get("rawOutput") or "").strip()
    for pattern, text in ((r"ENOTFOUND|EAI_AGAIN", "name not found"), (r"timed out|ETIMEDOUT", "timed out"),
                          (r"ECONNREFUSED", "connection refused"), (r"ENETUNREACH|EHOSTUNREACH", "unreachable"),
                          (r"ECONNRESET", "connection reset"), (r"certificate|CERT_|SELF_SIGNED|UNABLE_TO_VERIFY", "certificate error"),
                          (r"(?<![A-Za-z])(TLS|SSL)(?![A-Za-z])|EPROTO", "TLS error")):
        if re.search(pattern, raw, re.I):
            return text
    return code(raw.splitlines()[0][:60]) if raw else result.get("status", "?")


def alive(result):
    c = result.get("statusCode") if result.get("status") == "finished" else None
    return c is not None and (200 <= c < 300 or c in ACCEPT)


def location(result):
    c = result.get("statusCode") if result.get("status") == "finished" else None
    if c is None or not 300 <= c < 400:
        return None
    loc = next((v for k, v in (result.get("headers") or {}).items() if k.lower() == "location"), None)
    return loc[0] if isinstance(loc, list) else loc


def verdict(results):
    """("alive" | "down" | "tls" | "unchecked" | "redirect", reasons of the probes, (kind, evidence) of a dead page,
    or for "redirect" the address it leads to). A failure of the probe itself (failureSource internal) does not count,
    and fewer than MIN_READINGS readings judge nothing. "tls": every probe failed on the secure connection, as GitHub
    did; the checkers' TLS libraries refuse servers that browsers often still open (seen on vodio.fr, 24/11/2026)."""
    rs = [x for r in results for x in [r.get("result", {})]
          if x.get("status") == "finished" or (x.get("status") == "failed" and x.get("failureSource") != "internal")]
    reasons = [reason(r) for r in rs]
    if any(alive(r) for r in rs):
        found = next((f for r in rs if r.get("statusCode") == 200 and r.get("rawBody") for f in [classify(r["rawBody"])] if f), None)
        return "alive", reasons, found
    target = next((loc for r in rs for loc in [location(r)] if loc), None)
    if target:
        return "redirect", reasons, target
    if any(300 <= (r.get("statusCode") or 0) < 400 for r in rs):
        return "alive", reasons, None   # a redirect without an address: the server answers
    if len(rs) < MIN_READINGS:
        return "unchecked", reasons, None
    return ("tls" if all(x in ("TLS error", "certificate error") for x in reasons) else "down"), reasons, None


def _measure(urls, token, api, sleep):
    """{url: results} of one Globalping measurement per link; a link with no suitable probe is left out."""
    ids, out = {}, {}
    for url in urls:
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
                out[url] = m.get("results", [])
                break
            sleep(0.6)   # the API asks for 500 ms between two reads of one measurement
    return out


def recheck(urls, token=None, api=_api, sleep=time.sleep, confirm=True):
    """{url: (verdict, readings, dead page or None)} from Globalping, redirects followed (readings: one line per
    address read); links over the hourly limit are left out (unchecked)."""
    try:
        left = api("/limits", token=token)["rateLimit"]["measurements"]["create"]["remaining"]
    except Exception as e:
        left = 0
        print(f"::warning::Globalping: limits unreadable ({e}){' with GLOBALPING_TOKEN: check the token' if token else ''}", file=sys.stderr)
    print(f"Globalping: {left} tests left this hour ({'token' if token else 'anonymous'})", file=sys.stderr)   # read in the run log
    out, path, current = {}, {u: [] for u in urls}, {u: u for u in urls}
    pending = list(urls)
    for hop in range(HOPS + 1):
        pending = pending[: max(0, left) // PER_URL]
        if not pending:
            break
        left -= PER_URL * len(pending)
        results = _measure([current[u] for u in pending], token, api, sleep)
        nxt = []
        for u in pending:
            if current[u] not in results:
                continue
            v, reasons, extra = verdict(results[current[u]])
            if v == "redirect" and hop < HOPS:
                current[u] = urllib.parse.urljoin(current[u], extra)
                path[u].append(f"{', '.join(reasons)} to {code(current[u])}")   # the address comes from a third party
                nxt.append(u)
                continue
            if v == "redirect":
                v, extra = "alive", None   # still redirecting after HOPS: the server answers
            out[u] = (v, [*path[u], ", ".join(reasons)], extra)   # one line per address read: "301, 301, 301 to …", "404, 404, 404"
        pending = nxt
    doubt = [u for u in urls if out.get(u, ("",))[0] in ("down", "tls")]
    if confirm and doubt:   # a site down for a minute is not broken: read again later, broken only if it fails again
        if left >= PER_URL:
            sleep(CONFIRM_PAUSE)
            again = recheck(doubt, token, api, sleep, confirm=False)
        else:
            again = {}
        later = f"again {CONFIRM_PAUSE} seconds later"
        for u in doubt:
            v2 = again.get(u, ("unchecked", [], None))
            if v2[0] in ("down", "tls"):
                out[u] = (out[u][0], [*out[u][1], f"{later}: " + "; ".join(v2[1])], None)
            elif v2[0] == "unchecked":   # no second reading (hourly limit, service, probes): never broken on one reading
                out[u] = ("unchecked", [*out[u][1], f"not read {later}"], None)
            else:
                out[u] = v2
    return out


# --- Dead pages that answer 200 ---------------------------------------------------------------------------------

class _Reader(html.parser.HTMLParser):
    """Title, description, headings and visible text of a page, in one linear pass: counters, never a stack, so that
    unclosed or stray tags cost nothing."""
    SKIP = {"script", "style", "noscript", "svg", "template"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title, self.desc, self.heads, self.text, self.size = [], "", [], [], 0
        self.skip = self.in_title = self.in_head = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        elif tag == "title":
            self.in_title = 1
        elif tag in ("h1", "h2"):
            self.in_head += 1
        elif tag == "meta" and not self.desc:
            a = {k.lower(): (v or "") for k, v in attrs}
            if (a.get("name") or a.get("property") or "").lower() in ("description", "og:description"):
                self.desc = a.get("content", "")

    def handle_startendtag(self, tag, attrs):   # <svg ... />, <meta ... />: nothing opens
        if tag == "meta":
            self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self.skip = max(0, self.skip - 1)
        elif tag == "title":
            self.in_title = 0
        elif tag in ("h1", "h2"):
            self.in_head = max(0, self.in_head - 1)

    def handle_data(self, data):
        if self.skip:
            return
        if self.in_title:
            self.title.append(data)
        elif self.in_head:
            self.heads.append(data)
        if self.size < 3000:
            self.text.append(data)
            self.size += len(data)


def _text(page):
    """(title, description, headings, start of the visible text) of an HTML page."""
    r = _Reader()
    try:
        r.feed(page)
        r.close()
    except Exception:
        pass
    clean = lambda s: re.sub(r"\s+", " ", s).strip()
    return clean(" ".join(r.title)), clean(r.desc), clean(" ".join(r.heads)), clean(" ".join(r.text))[:3000]


def brand_words(root=ROOT):
    """Names of the brands of the directory (data/brands.toml), as words: a page about one is about bricks."""
    try:
        rows = tomllib.loads((root / "data" / "brands.toml").read_text(encoding="utf-8")).get("resource", [])
    except OSError:
        return []
    names = (n.split(" (")[0].strip().lower() for r in rows for n in [r.get("name", ""), *r.get("aliases", [])])
    return sorted({n for n in names if len(n) > 2})


def is_bricks(text):
    if not _BRANDS:
        _BRANDS.extend(brand_words() or ["lego"])
    t = text.lower()
    return bool(BRICKS.search(t)) or any(re.search(rf"(?<!\w){re.escape(w)}(?!\w)", t) for w in _BRANDS)


def classify(page):
    """(kind, evidence) for a dead page, else None. Kinds: parked or expired, taken over, closed. Parking and
    take-over are read in the title, the description and the main headings; a closure notice also in the start
    of the text."""
    title, desc, heads, start = _text(page)
    top = {"title": title, "description": desc, "heading": heads}
    for p in PARKED_SITE:
        if m := re.search(p, page, re.I):
            return "parked or expired", code(m.group(0))
    for p in PARKED_TEXT:
        for where, t in top.items():
            if m := re.search(p, t, re.I):
                return "parked or expired", f"{code(m.group(0))} in the {where}"
    if not is_bricks(" | ".join(top.values())):
        for p in TAKEN:
            for where, t in top.items():
                if m := re.search(p, t, re.I):
                    return "taken over", f"{code(m.group(0))} in the {where} {code(t[:90])}"
    for p in CLOSED:
        for where, t in (*top.items(), ("text", start)):
            if m := re.search(p, t, re.I):
                return "closed", f"{code(m.group(0))} in the {where}"
    return None


def _fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*;q=0.5"})
    with urllib.request.urlopen(req, timeout=20) as r:
        if r.status != 200 or "html" not in r.headers.get("Content-Type", "html"):
            return None
        raw = r.read(400_000)
        return raw.decode(r.headers.get_content_charset() or "utf-8", "replace")


def entries(root=ROOT):
    """[(id, url)] of every entry still open (status archived or dead left out), platforms left out."""
    out = []
    for path in sorted((root / "data").glob("*.toml")):
        for r in tomllib.loads(path.read_text(encoding="utf-8")).get("resource", []):
            host = (urllib.parse.urlsplit(r["url"]).hostname or "").removeprefix("www.")
            if r.get("status") not in ("archived", "dead") and not any(host == p or host.endswith("." + p) for p in PLATFORMS):
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


def reported(previous):
    """Links that the previous body reported as needing a look: its folded lists (alive, refused TLS) left out."""
    return set(re.findall(r"<(https?://[^>]+)>", re.sub(r"<details>.*?</details>", "", previous or "", flags=re.S)))


def order_for_recheck(urls, previous, today=None):
    """Links that failed in the previous run first, then the others in an order that changes each week, so that an
    hourly limit never leaves the same links out week after week."""
    today = today or dt.date.today()
    week = today.isocalendar()[:2]
    key = lambda u: hashlib.sha256(f"{week}{u}".encode()).hexdigest()
    before = reported(previous)
    return [u for u in urls if u in before] + sorted((u for u in urls if u not in before), key=key)


# --- Issue body -------------------------------------------------------------------------------------------------

def body(report, previous="", rechecked=None, dead=(), today=None):
    """(text, needs_a_person). rechecked=None: Globalping was not asked. A person is needed for a broken link,
    a dead page, or a link that failed twice in a row and could not be judged by Globalping."""
    today = today or dt.date.today()
    now = failures(report)
    before = reported(previous)
    rechecked = rechecked if rechecked is not None else {}
    v = lambda u: rechecked.get(u, ("unchecked",))[0]
    at = lambda u: f"{now[u][0]} {now[u][1]}"
    gh = lambda u: code(now[u][2])
    gp = lambda u: "; ".join(rechecked[u][1])
    order = lambda us: sorted(us, key=lambda u: now[u][:2])
    again = lambda u: " | also in the previous run" if u in before else ""
    broken = [u for u in now if v(u) == "down"]
    alive_dead = [(u, at(u), *rechecked[u][2]) for u in now if v(u) == "alive" and rechecked[u][2]]
    blocked = [u for u in now if v(u) == "alive" and not rechecked[u][2]]
    tls = [u for u in now if v(u) == "tls"]
    unchecked = [u for u in now if v(u) not in ("down", "alive", "tls")]
    known = {d[0] for d in dead}
    dead = sorted([*dead, *(x for x in alive_dead if x[0] not in known)])   # read by Globalping when GitHub could not
    opened = len(now) - len(unchecked)
    twice = [u for u in unchecked if u in before]
    once = [u for u in unchecked if u not in before]

    def text(fold):
        out = [(f"{plural(len(now), 'link', 'links')} failed from the machines of GitHub on {date_en(today)}"
                + (f"; {opened} {'was' if opened == 1 else 'were'} opened again from probes of Globalping on home and office networks."
                   if opened else ".")) if now else f"Every link answers from the machines of GitHub ({date_en(today)}).", ""]
        if broken:
            out += ["## Broken: they fail from GitHub and from every probe", ""]
            out += [f"* <{u}> ({at(u)}) | GitHub: {gh(u)} | Globalping: {gp(u)}{again(u)}" for u in order(broken)] + [""]
        if dead:
            out += ["## They answer, but the page is dead", ""]
            out += [f"* <{u}> ({where}) | {kind}: {ev}{again(u)}" for u, where, kind, ev in dead] + [""]
        if unchecked:
            out += ["## Not judged by Globalping (unavailable, over its hourly limit, or not read a second time)", "",
                    "Some sites refuse the machines of GitHub but open in a browser: open a link before changing its entry.", ""]
            for title, urls in (("Failed twice in a row", twice), ("Failed in this run only", once)):
                if urls:
                    out += [f"### {title}", ""] + [f"* <{u}> ({at(u)}) | {gh(u)}" + (f" | Globalping: {gp(u)}" if u in rechecked and gp(u) else "")
                                                   for u in order(urls)] + [""]
        for urls, summary in ((blocked, f"They block GitHub, alive according to Globalping on {date_en(today)}"),
                              (tls, "Their secure connection is refused by GitHub and by Globalping; a browser often still opens them")):
            if urls:
                shown = order(urls)[:fold]
                out += [f"<details><summary>{summary} ({len(urls)})</summary>", ""]
                out += [f"* <{u}> ({at(u)}) | GitHub: {gh(u)} | Globalping: {gp(u)}" for u in shown]
                out += ([f"* … and {len(urls) - len(shown)} more"] if len(shown) < len(urls) else []) + ["", "</details>", ""]
        if not now and not dead:
            out = [f"Every link answers ({date_en(today)}).", ""]
        return "\n".join(out)

    out = text(None)
    for fold in (200, 50, 10, 0):   # the folded lists give way first
        if len(out) <= LIMIT:
            break
        out = text(fold)
    if len(out) > LIMIT:
        out = out[:LIMIT].rsplit("\n", 1)[0] + "\n\n(cut: too long for an issue)\n"
    return out, bool(broken or dead or twice)


# --- Sample: the yardstick of the checks, read live --------------------------------------------------------------

def sample(path, token=None):
    """Reads each address of the sample and compares the verdict with the expected one (a list: any of them).
    A page that cannot be opened from here is read by Globalping, as the links issue does for a failure."""
    cases = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))["cases"]
    pages, unread = {}, []
    for c in (c for c in cases if c["check"] == "page"):
        try:
            page = _fetch(c["url"])
        except Exception:
            page = None
        if page is None:
            unread.append(c["url"])
        else:
            pages[c["url"]] = classify(page) or ("healthy", "")
    down = recheck([c["url"] for c in cases if c["check"] == "globalping"] + unread, token)
    for u in unread:
        x = down.pop(u, ("unchecked", [], None))
        pages[u] = x[2] or (("healthy", "read by Globalping") if x[0] == "alive" else ("unread", "; ".join(x[1])))
    bad = 0
    for c in cases:
        got, detail = (down.get(c["url"], ("unchecked", []))[0], "; ".join(down.get(c["url"], ("", []))[1])) if c["check"] == "globalping" else pages[c["url"]]
        ok = got in (c["expected"] if isinstance(c["expected"], list) else [c["expected"]])
        bad += not ok
        print(f"{'ok ' if ok else 'BAD'} {c['url']}: {got} (expected {c['expected']}) {detail}")
    print(f"{len(cases) - bad}/{len(cases)} as expected")
    return 1 if bad else 0


def main(argv):
    token = os.environ.get("GLOBALPING_TOKEN") or None
    if argv[:1] == ["--sample"]:
        return sample(argv[1], token)
    state = argv[argv.index("--state") + 1] if "--state" in argv else None
    args = [a for i, a in enumerate(argv) if not a.startswith("--") and not (i and argv[i - 1] == "--state")]
    read = lambda i: pathlib.Path(args[i]).read_text(encoding="utf-8") if len(args) > i and pathlib.Path(args[i]).exists() else ""
    report, previous = read(0), read(1)
    rechecked = recheck(order_for_recheck(list(failures(report)), previous), token) if "--recheck" in argv else None
    dead = dead_pages(entries()) if "--pages" in argv else ()
    text, needed = body(report, previous, rechecked, dead)
    if state:
        pathlib.Path(state).write_text("open" if needed else "close", encoding="utf-8")
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
