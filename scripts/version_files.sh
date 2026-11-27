#!/usr/bin/env bash
# What the workflow Version may write, and nothing else (scripts/changes.py, scripts/build.py, scripts/readme_image.py):
#   bash scripts/version_files.sh staged        the index after `git add -A` (build job)
#   bash scripts/version_files.sh patch FILE    a patch before `git apply` (publication job, which runs the copy of this
#                                               script taken from the commit of main, never one the patch could rewrite)
# Refused: any other path (a workflow, this script…), a rename or a copy, a symbolic link, an executable file.
set -euo pipefail
allowed='VERSION|CHANGELOG\.md|README\.md|full-list\.md|\.github/ISSUE_TEMPLATE/add-resource\.yml|media/site-preview(-dark)?\.png|changes/[a-z0-9]+(-[a-z0-9]+)*\.md'
bad=()
case "${1:-}" in
  staged)
    # --raw -z: ":<old mode> <new mode> <old sha> <new sha> <status>", then the path; --no-renames: a move is a deletion and an addition
    while IFS= read -r -d '' meta && IFS= read -r -d '' path; do
      read -r _ mode _ _ status <<< "${meta#:}"
      [[ "$path" =~ ^($allowed)$ ]] || bad+=("$status $path")
      case "$mode" in 100644|000000) ;; *) bad+=("mode $mode $path") ;; esac
    done < <(git diff --cached --no-renames --raw -z)
    ;;
  patch)
    [ -f "${2:-}" ] || { echo "::error::no patch to read"; exit 1; }
    while IFS=$'\t' read -r -d '' _ _ path; do
      [[ "$path" =~ ^($allowed)$ ]] || bad+=("$path")
    done < <(git apply --numstat -z "$2")
    while IFS= read -r line; do   # summary lines: only plain files created or deleted
      [[ "$line" =~ ^\ (create|delete)\ mode\ 100644\ ([^ ]+)$ ]] || bad+=("${line# }")
    done < <(git apply --summary "$2" | grep -E '^ (create|delete|rename|copy|mode)' || true)
    ;;
  *) echo "usage: version_files.sh staged | patch FILE" >&2; exit 2 ;;
esac
if [ ${#bad[@]} -gt 0 ]; then
  echo "::error::Version writes nothing but the version, its entry, the fragments and the generated files, as plain files; refused:"
  printf '%s\n' "${bad[@]}"
  exit 1
fi
