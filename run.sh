#!/usr/bin/env bash
# Linux / macOS launcher. Edit the settings below, then run:  ./run.sh
# A link given on the command line overrides URL:  ./run.sh https://github.com/some-user
set -euo pipefail
cd "$(dirname "$0")"

URL="https://github.com/storytold"
OUT_DIR="downloads"
OPTIONS=()   # for example: OPTIONS=(--dry-run --no-forks --prefer zip)

# GitHub allows only 60 API requests per hour without a token. Uncomment and paste yours
# (never commit a real token):
# export GITHUB_TOKEN="ghp_xxxxxxxx"

if [ -n "${1:-}" ]; then URL="$1"; fi

PY=python3
command -v "$PY" >/dev/null 2>&1 || PY=python
exec "$PY" get_latest.py "$URL" --dir "$OUT_DIR" ${OPTIONS[@]+"${OPTIONS[@]}"}
