#!/usr/bin/env bash
# Fetch a rolling year of your GitHub activity and render it to out/index.html.
# Usage: ./refresh.sh [--account NAME] [--end YYYY-MM-DD] [--days 366]
# Takes ~5 min: the collector paces itself under GitHub's search rate limit.
set -euo pipefail
cd "$(dirname "$0")"
python3 -m mergeprint.collect "$@"
python3 -m mergeprint.build --out out/index.html
echo
echo "out/index.html is ready (git-ignored). Open it locally, or share it deliberately:"
echo "  ./publish.sh            # push it to a gh-pages branch of your fork (public!)"
echo "  python3 -m mergeprint.build --out out/index.html --anonymize-repos   # hide repo names first"
