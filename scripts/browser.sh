#!/usr/bin/env bash
# Chromium (headless shell) and the system packages it needs, for scripts/check_site.py and scripts/readme_image.py
# on a GitHub runner (workflows Render and Version). Playwright comes from tests/requirements.txt.
#
# ~/fonts holds the packages kept by an earlier run (actions/cache): the fonts that Playwright installs came at
# 60 kB/s from the Ubuntu mirror on some runs. KEPT_THIS_WEEK=true (exact hit of the weekly key): they are installed
# directly with dpkg (not checked against the signed index of apt: the cache of main is written only by runs on main),
# without `apt-get update` and the resolution of `--with-deps`, and Playwright then checks that
# nothing it needs is missing; if anything is, or on any other run, `--with-deps` as before, and ~/fonts is filled
# again with the packages of the versions now installed (saved by the workflow, from main only).
set -euo pipefail
t0=$SECONDS
lap() { echo "[$(( SECONDS - t0 )) s] $1"; }
kept=$HOME/fonts
direct=false
if [ "${KEPT_THIS_WEEK:-}" = true ] && compgen -G "$kept/*.deb" > /dev/null; then
  newer=()   # only a package missing or older on the runner: an image updated during the week is never downgraded
  for f in "$kept"/*.deb; do
    pkg=$(dpkg-deb -f "$f" Package) ver=$(dpkg-deb -f "$f" Version)
    cur=$(dpkg-query -W -f='${Version}' "$pkg" 2>/dev/null || true)
    if [ -z "$cur" ] || dpkg --compare-versions "$ver" gt "$cur"; then newer+=("$f"); fi
  done
  if [ ${#newer[@]} -eq 0 ] || sudo dpkg -i "${newer[@]}" > /dev/null; then direct=true; fi
  lap "kept packages installed with dpkg ($direct)"
fi
python3 -m playwright install --only-shell chromium   # check_site.py and readme_image.py launch the headless shell only
lap "headless shell"
if [ "$direct" = true ] && python3 -m playwright install-deps --dry-run chromium; then
  lap "system packages: kept ones, nothing missing"
  exit 0
fi
if compgen -G "$kept/*.deb" > /dev/null; then sudo cp "$kept"/*.deb /var/cache/apt/archives/; fi
sudo apt-get install -f -y -qq > /dev/null 2>&1 || true   # a failed dpkg above leaves packages to configure
python3 -m playwright install-deps chromium
lap "system packages: --with-deps"
# kept for the next runs: the packages of the versions now installed, and no others (older ones would pile up week after week)
rm -rf "$kept" && mkdir "$kept"
for f in /var/cache/apt/archives/*.deb; do
  [ -e "$f" ] || continue
  pkg=$(dpkg-deb -f "$f" Package) ver=$(dpkg-deb -f "$f" Version)
  if [ "$(dpkg-query -W -f='${Version}' "$pkg" 2>/dev/null)" = "$ver" ]; then cp "$f" "$kept/"; fi
done
ls "$kept"
if [ -n "${GITHUB_OUTPUT:-}" ]; then echo "kept=$(find "$kept" -name '*.deb' | wc -l)" >> "$GITHUB_OUTPUT"; fi
