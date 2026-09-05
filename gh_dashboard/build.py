"""Inline raw.json + config + holidays into template.html -> out/index.html.

Usage: python3 -m gh_dashboard.build [--raw raw.json] [--out
out/index.html] [--anonymize-repos]
                                     [--public-only] [--exclude-repo GLOB
...] [--config FILE]

All aggregation happens in the page itself, so holidays, timezone and
days off can be
changed in the browser without rebuilding. Only PR-level timestamps,
sizes and repo names
are inlined; never titles, bodies or URLs.
"""

import argparse
import datetime as dt
import json
import os
from html import escape
from pathlib import Path

from .settings import add_repo_args, cli_config, repo_filter

D = os.path.dirname(os.path.abspath(__file__))


def main(argv=None):
    cfg = cli_config(argv)
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--raw", default="raw.json")
    ap.add_argument("--out", default="out/index.html")
    ap.add_argument(
        "--anonymize-repos",
        action="store_true",
        help="replace repository names with repo-1, repo-2, ...",
    )
    add_repo_args(ap, cfg)
    a = ap.parse_args(argv)
    raw = json.loads(Path(a.raw).read_text(encoding="utf-8"))
    keep = repo_filter(a, raw.get("private", []))

    loc = {
        (repo, pr["number"]): pr
        for repo, rows in raw["loc"].items()
        for pr in rows
    }
    repos, prs = [], []
    for line in raw["prs"]:
        num, created, closed, merged, repo = line.split("\t")
        if not keep(repo):
            continue
        if repo not in repos:
            repos.append(repo)
        size_data = loc.get((repo, int(num)))
        size = (
            [
                size_data["additions"],
                size_data["deletions"],
                size_data["changedFiles"],
            ]
            if size_data
            else None
        )
        prs.append(
            [created, closed, merged, repos.index(repo), size, int(num)]
        )
    issues = []
    for line in raw["issues"]:
        _, created, _, _, repo = line.split("\t")
        if keep(repo):
            if repo not in repos:
                repos.append(repo)
            issues.append([created, repos.index(repo)])
    loc_idx = [repos.index(r) for r in raw["loc"] if r in repos]
    if a.anonymize_repos:
        repos = [f"repo-{i + 1}" for i in range(len(repos))]

    data = {
        "account": raw["account"],
        "start": raw["start"],
        "end": raw["end"],
        "repos": repos,
        "prs": prs,
        "locRepos": loc_idx,
        "issues": issues,
        "backlogComplete": raw.get("backlog_complete", False),
        "collectedAt": raw.get("collected_at"),
        "anonymized": a.anonymize_repos,
        "bigPr": cfg["big_pr"],
        "settings": {
            "country": cfg["country"],
            "timezone": cfg["timezone"],
            "holidays": cfg["holidays"],
            "offDays": cfg["off_days"],
            "events": cfg["events"],
        },
        "holidays": json.loads(
            Path(D, "holidays.json").read_text(encoding="utf-8")
        ),
    }

    blob = json.dumps(data, separators=(",", ":")).replace("<", "\\u003c")

    def fmt(value):
        date = dt.date.fromisoformat(value)
        return f"{date.day} {date:%b %Y}"

    html = (
        Path(D, "template.html")
        .read_text(encoding="utf-8")
        .replace("__ACCOUNT__", escape(data["account"]))
        .replace("__RANGE__", f"{fmt(raw['start'])} - {fmt(raw['end'])}")
        .replace("__DATA__", blob)
    )
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    Path(a.out).write_text(html, encoding="utf-8")
    print(
        f"wrote {a.out}: {len(prs)} PRs, "
        f"{len(data['issues'])} issues, {len(repos)} repos"
    )


if __name__ == "__main__":
    main()
