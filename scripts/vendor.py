#!/usr/bin/env python3
"""Copy the third-party files the website serves from the npm packages locked in package-lock.json.

The website needs no npm at build time: MiniSearch and the fonts of the Brick Vault are kept in the
repository. Their versions live in package.json, so Renovate proposes their updates like any other
dependency; after such an update, run this script and commit what it changes.

Usage: npm ci --ignore-scripts && python3 scripts/vendor.py [--check]
  --check  change nothing; fail if a kept file differs from what the locked packages give
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
NM = ROOT / "node_modules"


def version(pkg):
    return json.loads((NM / pkg / "package.json").read_text(encoding="utf-8"))["version"]


def minisearch():
    src = NM / "minisearch" / "dist" / "umd" / "index.js"
    out = subprocess.run(["npx", "--no-install", "terser", str(src), "--compress", "--mangle", "--comments", "false"],
                         cwd=ROOT, check=True, capture_output=True, text=True).stdout
    head = f"/*! MiniSearch {version('minisearch')} — (c) Luca Ongaro — licence MIT — https://github.com/lucaong/minisearch */\n"
    return (head + out.strip() + "\n").encode("utf-8")


def files():
    """{path in the repository: bytes it should hold}"""
    fs, ps = NM / "@fontsource-variable" / "nunito", NM / "@fontsource" / "press-start-2p"
    return {
        "site-src/vendor/minisearch.min.js": minisearch(),
        "site-src/vendor/minisearch-LICENSE.txt": (NM / "minisearch" / "LICENSE.txt").read_bytes(),
        "media/fonts/nunito.woff2": (fs / "files" / "nunito-latin-wght-normal.woff2").read_bytes(),
        "media/fonts/nunito-LICENSE.txt": (fs / "LICENSE").read_bytes(),
        "media/fonts/press-start-2p.woff2": (ps / "files" / "press-start-2p-latin-400-normal.woff2").read_bytes(),
        "media/fonts/press-start-2p-LICENSE.txt": (ps / "LICENSE").read_bytes(),
    }


def main():
    check = "--check" in sys.argv[1:]
    if not NM.is_dir():
        sys.exit("node_modules is missing: run npm ci --ignore-scripts first")
    differ = []
    for rel, data in files().items():
        path = ROOT / rel
        if path.exists() and path.read_bytes() == data:
            continue
        differ.append(rel)
        if not check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    if check and differ:
        print("::error::Kept third-party files differ from the locked packages: " + ", ".join(differ)
              + ". Run `npm ci --ignore-scripts && python3 scripts/vendor.py`, then `python3 scripts/build.py`, and commit.")
        sys.exit(1)
    print("✓ " + (("updated: " + ", ".join(differ)) if differ and not check else "kept third-party files match the locked packages"))


if __name__ == "__main__":
    main()
