# Mergeprint

**See what you actually shipped.** PR throughput, backlog, merge time, sizes and period-over-period
trends, built locally from the `gh` CLI. The contribution graph says you were busy; this says what landed.

`local-first` · `private repos supported` · `one self-contained HTML report`

**[Live demo](https://kirilklein.github.io/mergeprint/)**

[![Mergeprint demo](https://raw.githubusercontent.com/kirilklein/mergeprint/main/docs/screenshot.png)](https://kirilklein.github.io/mergeprint/)

## One command

```bash
uvx mergeprint        # or: pipx run mergeprint
```

Needs Python 3.9+ and the [`gh` CLI](https://cli.github.com/) logged in. Nothing else.
Bleeding edge: `uvx --from git+https://github.com/kirilklein/mergeprint mergeprint`.

```
GitHub account [octodev]:
Days to cover [366]:
Public repositories only (private activity never touches disk) [Y/n]:
Repositories to exclude, comma-separated globs like acme/*:
Timezone (IANA name) [Europe/Berlin]:
Country code for public holidays [DE]:
```

Enter keeps every default. About five minutes later `out/index.html` opens in your browser. Then use
**Settings** on the page for days off and events: every number recomputes instantly, nothing is
rebuilt. `mergeprint --yes` skips the questions, `--no-open` skips the browser.

Prefer a clone? `git clone https://github.com/kirilklein/mergeprint && cd mergeprint && ./refresh.sh`.

## Explore your report

- **Overview:** four headline metrics, trailing cadence, monthly activity, repository search, and highlights.
- **Explore:** cumulative progress, historical backlog, size vs. wait, merge timing, lines moved, and expandable top-five records.
- **Filters:** choose 30 days, 90 days, or the full collected range, or enter your own dates. Repository selection applies to both PRs and issues. The repository table remains an overview so you can switch between repositories.
- **Comparisons:** equal-length preceding periods, only when both fit inside the collected data. Counts and business-day rates appear together.
- **Settings:** timezone, country holidays, time off, events, and hiding repository names for screenshots. Light, dark, and automatic themes are supported.

Older `raw.json` files still build, but the backlog chart asks you to collect again because those
snapshots did not include open PRs. A saved report is a snapshot, not a live inbox.

## Your data stays yours

- Fetched data (`raw.json`), your answers (`config.local.json`) and the built page (`out/`) are
  written to the current directory and git-ignored. Nothing personal can end up in a fork by accident.
- The page is one self-contained HTML file. It makes no requests (fonts aside) and stores your
  settings in your browser only.
- Sharing is a separate, explicit step: send the file, or run `./publish.sh`, which asks before it
  pushes to a public `gh-pages` branch.
- A shareable version without repository names: `--anonymize-repos` on the build. Without private
  repos at all: answer yes to *public only* and the search itself excludes them, so they never reach disk.

## More control

```bash
python3 -m mergeprint.collect --account someone-else --end 2026-06-30 --days 180
python3 -m mergeprint.collect --exclude-repo 'acme/*' --exclude-repo octodev/dotfiles
python3 -m mergeprint.build --out out/index.html --anonymize-repos
```

Persistent defaults live in `config.local.json` (same keys as `mergeprint/config.json`):

```json
{"timezone": "Europe/Berlin", "country": "DE", "public_only": true,
 "off_days": ["2026-07-06..2026-07-24"], "events": [["2026-03-25", "conference"]]}
```

## Using a coding agent

The repo is small and documented for agents (`AGENTS.md`). One-line asks that work well:

- "Run `mergeprint` and open the result."
- "Add my vacation from 6 to 24 July to the config and rebuild."
- "Add a chart of merges per repository per month."
- "Build a version without repo names and publish it to gh-pages."

## How it works

`collect.py` uses `gh api search/issues` for authored PRs overlapping the period, including still-open
PRs and PRs closed after the selected end date, and for issues opened in the period. Dense date
ranges are split to respect GitHub's search cap; incomplete results stop collection rather than
produce a partial report. `gh pr list` supplies sizes for the busiest repositories. `build.py` inlines
those rows, your defaults and a bundled public-holiday table (250 countries, via the
[`holidays`](https://github.com/vacanza/holidays) package at generation time) into `template.html`.
All aggregation happens in the page, in plain JavaScript with inline SVG charts.

Conventions:

- **Business days** exclude weekends, the chosen country's public holidays and your days off. An
  unlisted day off inflates the denominator, so the per-business-day rate is a floor.
- **Lines of code** count only PRs at or below `big_pr` (10,000) changed lines. Size coverage is
  reported explicitly; the threshold does not determine whether code is generated or vendored.
- **Issues** are counted by creation date: issues *opened* by the account.
- **Timestamps** are converted to the chosen timezone in the browser, DST-aware.
- **Backlog** uses creation and closure timestamps, including PRs closed after the selected window.
  The final partial week ends at the selected date. Reopen cycles are not reconstructed.
- **Merge timing** describes when PRs landed, including merges performed by maintainers. It does
  not measure the author's working hours or impact.

## Development checks

```bash
./demo.sh
python3 -m py_compile mergeprint/*.py demo/*.py tools/*.py
python3 -m unittest discover -s tests -v
node --test tests/metrics.cjs
uvx --from . mergeprint --help
```

Node is needed only for the aggregation tests, not to build or view a report. In a browser, check
both views, the date and repository filters, records, settings, and mobile layout.

The demo is a deterministic synthetic year for a fictional `octodev`; `./demo.sh` regenerates it into
`docs/index.html`, the only built page tracked in git.

MIT licensed.
