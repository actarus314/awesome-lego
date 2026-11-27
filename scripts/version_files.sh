#!/usr/bin/env bash
# The files staged by the workflow Version are only those it writes (scripts/changes.py, scripts/build.py,
# scripts/readme_image.py): run after `git add -A` in its build job, and after `git apply --index` in its publication job.
set -euo pipefail
allowed='VERSION|CHANGELOG\.md|README\.md|full-list\.md|\.github/ISSUE_TEMPLATE/add-resource\.yml|media/site-preview(-dark)?\.png|changes/[^/]+'
other=$(git diff --cached --name-only | grep -vxE "$allowed" || true)
if [ -n "$other" ]; then
  echo "::error::Version writes nothing but the version, its entry, the fragments and the generated files; staged as well:"
  echo "$other"
  exit 1
fi
