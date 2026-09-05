# gh-dashboard

Your year on GitHub as one interactive page: merged PRs, cadence per business day, PR size vs.
time-to-merge, a weekday x hour heatmap, the shape of an average working day, lines moved. Built
locally from the `gh` CLI, nothing leaves your machine.

**[Live demo](https://kirilklein.github.io/gh-dashboard/)**

[![gh-dashboard demo](https://raw.githubusercontent.com/kirilklein/gh-dashboard/main/docs/screenshot.png)](https://kirilklein.github.io/gh-dashboard/)

## One command

```bash
uvx gh-dashboard        # or: pipx run gh-dashboard
```

Needs Python 3.9+ and the [`gh` CLI](https://cli.github.com/) logged in. Nothing else.
Bleeding edge: `uvx --from git+https://github.com/kirilklein/gh-dashboard gh-dashboard`.

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
rebuilt. `gh-dashboard --yes` skips the questions, `--no-open` skips the browser.

Prefer a clone? `git clone https://github.com/kirilklein/gh-dashboard && cd gh-dashboard && ./refresh.sh`.

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
python3 -m gh_dashboard.collect --account someone-else --end 2026-06-30 --days 180
python3 -m gh_dashboard.collect --exclude-repo 'acme/*' --exclude-repo octodev/dotfiles
python3 -m gh_dashboard.build --out out/index.html --anonymize-repos
```

Persistent defaults live in `config.local.json` (same keys as `gh_dashboard/config.json`):

```json
{"timezone": "Europe/Berlin", "country": "DE", "public_only": true,
 "off_days": ["2026-07-06..2026-07-24"], "events": [["2026-03-25", "conference"]]}
```

## Using a coding agent

The repo is small and documented for agents (`AGENTS.md`). One-line asks that work well:

- "Run `gh-dashboard` and open the result."
- "Add my vacation from 6 to 24 July to the config and rebuild."
- "Add a chart of merges per repository per month."
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

The demo is a deterministic synthetic year for a fictional `octodev`; `./demo.sh` regenerates it into
`docs/index.html`, the only built page tracked in git.

MIT licensed.
