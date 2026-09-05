#!/usr/bin/env bash
# Publish out/index.html to the gh-pages branch of this repo's origin. Opt-in and loud:
# once pushed, the page (and your activity data inside it) is public.
set -euo pipefail
cd "$(dirname "$0")"
[ -f out/index.html ] || { echo "out/index.html missing - run ./refresh.sh first"; exit 1; }
remote=$(git remote get-url origin)
echo "This pushes your activity dashboard to gh-pages on: $remote"
read -r -p "Make it public? [y/N] " ok
[ "$ok" = "y" ] || exit 0
tmp=$(mktemp -d)
cp out/index.html "$tmp/index.html"
git -C "$tmp" init -q -b gh-pages
git -C "$tmp" add index.html
git -C "$tmp" -c user.name=mergeprint -c user.email=mergeprint@localhost commit -q -m "publish dashboard"
git -C "$tmp" push -f "$remote" gh-pages
rm -rf "$tmp"
echo "Pushed. Enable Pages (branch gh-pages) in the repo settings if you haven't."
