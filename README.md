# gh-dashboard

A one-page, interactive dashboard of your last year on GitHub: merged PRs, cadence per business
day, cumulative progress with your own annotations, PR size vs. time-to-merge, weekly flow,
a weekday x hour heatmap in your timezone, the shape of an average working day, and lines moved.

**[Live demo](https://kirilklein.github.io/gh-dashboard/)** (synthetic account) · everything below runs locally.

Requirements: Python 3.9+ and the [`gh` CLI](https://cli.github.com/) logged in. No other dependencies.

## Your data stays yours

- Fetched data (`raw.json`), your settings (`config.local.json`) and your built page (`out/`) are
  git-ignored. Nothing personal can end up in a fork by accident.
- The page is a single self-contained HTML file. It makes no requests (fonts aside) and stores your
  settings in your browser only.
- Sharing is a separate, explicit step: send the file, or run `./publish.sh`, which asks before it
  pushes to a public `gh-pages` branch.
- Want a shareable version without repository names? `--anonymize-repos`. Without private repos at
  all? `--public-only` on `collect.py` keeps them off your disk in the first place.

## Quick start

```bash
git clone https://github.com/kirilklein/gh-dashboard && cd gh-dashboard
./refresh.sh                 # ~5 min, paced under GitHub's search rate limit
open out/index.html          # or xdg-open / start
```

Then open **Settings** on the page: pick your country for public holidays, your timezone, paste
your days off, add a few events. Every number recomputes instantly; nothing is rebuilt.

### Options

```bash
./refresh.sh --account someone-else --end 2026-06-30 --days 180
python3 collect.py --public-only                       # never fetch private-repo activity
python3 collect.py --exclude-repo 'acme/*' --exclude-repo octodev/dotfiles
python3 build.py --out out/index.html --anonymize-repos # repo-1, repo-2, ... for sharing
```

Persistent defaults go in `config.local.json` (ignored by git; same keys as `config.json`):

```json
{"timezone": "Europe/Berlin", "country": "DE", "public_only": true,
 "off_days": ["2026-07-06..2026-07-24"], "events": [["2026-03-25", "conference"]]}
```

## Using a coding agent

The repo is small and documented for agents (`AGENTS.md`). Things that work well as one-line asks:

- "Run `./refresh.sh` and open the result."
- "Add my vacation from 6 to 24 July to the config and rebuild."
- "Add a chart of merges per repository per month."
- "Change the accent colour to blue."
- "Build a version without repo names and publish it to gh-pages."

## How it works

`collect.py` uses `gh api search/issues` month by month (PRs closed and issues opened by the
account) plus `gh pr list` on the busiest repositories for additions/deletions. `build.py` inlines
those rows, your defaults and a bundled public-holiday table (250 countries, via the
[`holidays`](https://github.com/vacanza/holidays) package at generation time) into `template.html`.
All aggregation happens in the page, in plain JavaScript with inline SVG charts.

Conventions:

- **Business days** exclude weekends, the chosen country's public holidays and your days off. An
  unlisted day off inflates the denominator, so the per-business-day rate is a floor.
- **Lines of code** count only PRs under `big_pr` (10,000) changed lines; bigger ones are almost
  always generated or vendored bulk that swamps the signal.
- **Issues** are counted by creation date: issues *opened* by the account.
- **Timestamps** are converted to the chosen timezone in the browser, DST-aware.

## Demo

`./demo.sh` regenerates `dist/index.html` from `demo/raw.json`, a deterministic synthetic year for
a fictional `octodev`. That is the only built page tracked in git.

MIT licensed.
