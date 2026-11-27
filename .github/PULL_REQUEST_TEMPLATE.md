**What changes, and why:**

**Kind of change:** data (`data/`) · website (`site-src/`, `scripts/build.py`) · automation (`scripts/`, `.github/workflows/`) · documentation

**Sources, for a data change (links with date):**

- [ ] `python3 scripts/build.py` and `python3 -m unittest discover -s tests` pass; `changes/<name>.md` says what changes; `VERSION`, `CHANGELOG.md` and the generated files left as on `main`
- [ ] Data: only `data/*.toml` edited by hand, never the generated files
- [ ] Data: no affiliate or referral link
- [ ] Website or automation: what was run to check it, or the preview link, is written above
