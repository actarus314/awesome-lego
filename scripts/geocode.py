#!/usr/bin/env python3
"""Fill data/backend/geocode.json with the coordinates of the cities of places, events and clubs.

Usage: python3 scripts/geocode.py [--check]   (standard library only)

One query per city not yet in the file, to the public Nominatim service of OpenStreetMap, following its usage
policy (https://operations.osmfoundation.org/policies/nominatim/): at most one request per second, an identifying
User-Agent, results kept in the file so that a city is never asked twice. Coordinates are those of the city, not of
an address: enough to place an entry on a map and sort by distance. `--check` only lists the cities still missing
(exit code 1 if any), without network access.
"""
import datetime as dt
import json
import pathlib
import sys
import time
import tomllib
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "backend" / "geocode.json"
UA = "awesome-lego-geocode/1.0 (+https://github.com/actarus314/awesome-lego)"


def cities(r):
    """'Chambéry, Annecy' is two cities; each gets its own point."""
    return [c.strip() for c in str(r.get("city", "")).split(",") if c.strip()]


def key(city, r):
    cc = [c for c in r.get("countries", []) if c != "international"]
    return f"{city}|{cc[0] if len(cc) == 1 else ''}"


def wanted():
    out = {}
    for path in sorted((ROOT / "data").glob("*.toml")):
        if path.stem in ("journeys",):
            continue
        for r in tomllib.loads(pathlib.Path(path).read_text(encoding="utf-8")).get("resource", []):
            for c in cities(r):
                out.setdefault(key(c, r), []).append(r["id"])
    return out


def main():
    cache = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {
        "source": "https://nominatim.openstreetmap.org/", "date": "", "kind": "read",
        "licence": "Data © OpenStreetMap contributors, ODbL 1.0, https://osm.org/copyright", "places": {}}
    want = wanted()
    missing = [k for k in want if k not in cache["places"]]
    if "--check" in sys.argv:
        for k in missing:
            print("✗ no coordinates for", k, "used by", ", ".join(want[k]))
        sys.exit(1 if missing else 0)
    for i, k in enumerate(missing):
        city, cc = k.split("|")
        q = {"q": city, "format": "jsonv2", "limit": 1, "accept-language": "en"}
        if cc:
            q["countrycodes"] = cc.lower()
        req = urllib.request.Request("https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(q), headers={"User-Agent": UA})
        if i:
            time.sleep(3)  # usage policy: one request per second at most
        found = None
        for wait in (0, 10, 30):  # a refusal for load (HTTP 429 or 629) is retried later, never in a loop
            time.sleep(wait)
            try:
                with urllib.request.urlopen(req, timeout=20) as resp:
                    found = json.load(resp)
                break
            except OSError as exc:
                err = exc
        if found is None:
            print("✗", k, err, file=sys.stderr)
            continue
        if not found:
            print("✗ not found:", k, file=sys.stderr)
            continue
        f = found[0]
        cache["places"][k] = {"lat": round(float(f["lat"]), 4), "lon": round(float(f["lon"]), 4),
                              "osm": f"{f.get('osm_type', '')}/{f.get('osm_id', '')}", "name": f.get("display_name", "")}
        print("✓", k, cache["places"][k]["lat"], cache["places"][k]["lon"], f.get("display_name", "")[:70])
    unused = [k for k in cache["places"] if k not in want]
    for k in unused:
        del cache["places"][k]
    if missing or unused:
        cache["date"] = dt.date.today().isoformat()
        cache["places"] = dict(sorted(cache["places"].items()))
        OUT.write_text(json.dumps(cache, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
