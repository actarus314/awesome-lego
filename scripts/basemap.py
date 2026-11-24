#!/usr/bin/env python3
"""Write media/basemap.json, the background of the "Out and about" map: country outlines and reference cities.

Usage: python3 scripts/basemap.py   (standard library only; run again only to change the drawing)

Source: Natural Earth (public domain, https://www.naturalearthdata.com/), 1:50m countries and 1:10m populated
places, read from a fixed commit of the project's GitHub repository. Outlines are projected once (Web Mercator, latitudes -60 to 78,
world 1000 units wide), simplified and rounded, so that the website only draws paths; the website places the
points of the entries with the same projection. Reference cities: per country its capital and its three largest
cities, with their English and French names.
"""
import datetime as dt
import json
import math
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "media" / "basemap.json"
BASE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/ca96624a56bd078437bca8184e78163e5039ad19/geojson/"  # a fixed commit: the drawing changes only when this line does
UA = "awesome-lego-basemap/1.0 (+https://github.com/actarus314/awesome-lego)"
W = 1000.0
TOL = 0.4  # simplification tolerance, in map units (the world is 1000 wide)


def proj(lon, lat):
    lat = max(-60.0, min(78.0, lat))
    y = math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    return (lon + 180) / 360 * W, (1 - y / math.pi) / 2 * W


def simplify(pts, tol):
    """Douglas-Peucker, iterative."""
    if len(pts) < 4:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        (x1, y1), (x2, y2) = pts[a], pts[b]
        dx, dy = x2 - x1, y2 - y1
        n = math.hypot(dx, dy)
        best, idx = 0.0, None
        for i in range(a + 1, b):
            d = abs(dy * pts[i][0] - dx * pts[i][1] + x2 * y1 - y2 * x1) / n if n > 1e-9 else math.hypot(pts[i][0] - x1, pts[i][1] - y1)  # closed ring
            if d > best:
                best, idx = d, i
        if idx is not None and best > tol:
            keep[idx] = True
            stack += [(a, idx), (idx, b)]
    return [p for p, k in zip(pts, keep) if k]


def area(pts):
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]))) / 2


def path(pts):
    """SVG path in tenths of a unit, relative steps after the first point: much shorter text."""
    q = [(round(x * 10), round(y * 10)) for x, y in pts[:-1]]
    q = [b for a, b in zip([None] + q, q) if b != a]
    steps = " ".join(f"{(b[0] - a[0]) / 10:g} {(b[1] - a[1]) / 10:g}" for a, b in zip(q, q[1:]))
    return (f"M{q[0][0] / 10:g} {q[0][1] / 10:g}l{steps}z").replace(" -", "-")


def get(name):
    req = urllib.request.Request(BASE + name, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def main():
    countries = []
    for f in get("ne_50m_admin_0_countries.geojson")["features"]:
        p, g = f["properties"], f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        rings = []
        for poly in polys:  # outer rings only: lakes and holes add weight and little to read
            pts = simplify([proj(x, y) for x, y in poly[0]], TOL)
            rings.append((area(pts), pts))
        rings.sort(key=lambda r: -r[0])
        d = [path(pts) for i, (a, pts) in enumerate(rings) if len(pts) >= 4 and (i == 0 or a >= 0.05)]  # a country keeps at least its largest part
        if not d:
            continue
        iso = p["ISO_A2"] if p["ISO_A2"] not in ("-99", None) else p["ISO_A2_EH"]
        lx, ly = proj(p["LABEL_X"], p["LABEL_Y"])
        countries.append({"c": iso, "k": p["CONTINENT"], "x": round(lx, 1), "y": round(ly, 1), "d": "".join(d)})
    by = {}
    for f in get("ne_10m_populated_places.geojson")["features"]:
        p = f["properties"]
        by.setdefault(p["ISO_A2"], []).append(p)
    places = []
    for iso, ps in by.items():
        caps = [p for p in ps if p["ADM0CAP"] == 1][:1]
        big = [p for p in sorted(ps, key=lambda p: -p["POP_MAX"]) if p not in caps][:3]
        for rank, p in [(0, p) for p in caps] + [(i + 1, p) for i, p in enumerate(big)]:
            x, y = proj(p["LONGITUDE"], p["LATITUDE"])
            places.append({"en": p["NAME_EN"] or p["NAME"], "fr": p["NAME_FR"] or p["NAME"], "c": iso, "r": rank, "x": round(x, 1), "y": round(y, 1)})
    out = {"source": "Natural Earth 1:50m countries and 1:10m populated places (public domain)", "url": "https://www.naturalearthdata.com/",
           "date": dt.date.today().isoformat(), "projection": "Web Mercator, latitudes -60 to 78, world 1000 units wide",
           "countries": countries, "places": places}
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"✓ {OUT.relative_to(ROOT)}: {len(countries)} countries, {len(places)} places, {OUT.stat().st_size} bytes")


if __name__ == "__main__":
    main()
