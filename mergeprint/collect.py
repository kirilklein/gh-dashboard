"""Fetch a rolling year of GitHub activity for one account into raw.json.

Usage: python3 -m mergeprint.collect [--account NAME] [--end YYYY-MM-
DD] [--days 366]
                                       [--public-only] [--exclude-repo
GLOB ...] [--out raw.json]

Uses the `gh` CLI and whatever account it is logged in as. Nothing is
sent anywhere
else; raw.json stays on disk and is git-ignored. With --public-only the
search itself is
restricted to public repositories, so private activity never reaches the
disk.
"""

import argparse
import collections
import datetime as dt
import json
import subprocess
import sys
import time

from .settings import add_repo_args, cli_config, repo_filter


def gh(*args):
    r = subprocess.run(["gh", *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[:200])
    return r.stdout


def search(q, start=None, end=None, field="closed"):
    """Split dense date ranges to respect the 1,000-result search cap."""
    rows, page = [], 1
    query = f"{q} {field}:{start}..{end}" if start else q
    while page <= 10:
        for attempt in range(3):
            try:
                out = json.loads(
                    gh(
                        "api",
                        "-X",
                        "GET",
                        "search/issues",
                        "-f",
                        f"q={query}",
                        "-f",
                        "per_page=100",
                        "-f",
                        f"page={page}",
                    )
                )
                break
            except RuntimeError as e:
                transient = any(
                    s in str(e).lower()
                    for s in (
                        "rate limit",
                        "http 429",
                        "http 500",
                        "http 502",
                        "http 503",
                        "http 504",
                    )
                )
                if not transient or attempt == 2:
                    raise
                print(f"  retry p{page}: {e}", flush=True)
                time.sleep(45)
        if out.get("incomplete_results"):
            raise RuntimeError(
                "GitHub returned incomplete search results; "
                "retry collection later."
            )
        if out["total_count"] > 1000:
            if start and start < end:
                mid = start + (end - start) // 2
                return search(q, start, mid, field) + search(
                    q, mid + dt.timedelta(1), end, field
                )
            raise RuntimeError(
                "Search exceeds 1,000 results in one day or an undated query."
            )
        items = out["items"]
        rows += [
            "\t".join(
                [
                    str(p["number"]),
                    p["created_at"],
                    p.get("closed_at") or "",
                    p.get("pull_request", {}).get("merged_at") or "",
                    p["repository_url"].removeprefix(
                        "https://api.github.com/repos/"
                    ),
                ]
            )
            for p in items
        ]
        print(f"  {query} p{page}: {len(items)}", flush=True)
        time.sleep(3)
        if page * 100 >= out["total_count"]:
            break
        page += 1
    return rows


def main(argv=None):
    cfg = cli_config(argv)
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--account", default=cfg["account"])
    ap.add_argument("--end", default=dt.date.today().isoformat())
    ap.add_argument("--days", type=int, default=cfg["days"])
    ap.add_argument("--out", default="raw.json")
    add_repo_args(ap, cfg)
    a = ap.parse_args(argv)
    if a.days < 1:
        ap.error("--days must be at least 1")
    account = a.account or gh("api", "user", "--jq", ".login").strip()
    end = dt.date.fromisoformat(a.end)
    start = end - dt.timedelta(a.days - 1)
    if end > dt.date.today():
        ap.error("--end cannot be in the future")
    # UTC padding retains events falling on a boundary date in the
    # selected timezone.
    padded_start, padded_end = start - dt.timedelta(1), end + dt.timedelta(1)
    vis = " is:public" if a.public_only else ""
    print(f"account {account}, {start} .. {end}{vis}")

    out = {
        "account": account,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "prs": [],
        "issues": [],
        "loc": {},
        "private": [],
        "backlog_complete": True,
        "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    out["prs"] = search(
        f"is:pr author:{account} is:closed created:<={padded_end}{vis}",
        padded_start,
        dt.date.today() + dt.timedelta(1),
    )
    out["prs"] += search(
        f"is:pr author:{account} is:open created:<={padded_end}{vis}"
    )
    out["prs"] = list(
        {(r.split("\t")[4], r.split("\t")[0]): r for r in out["prs"]}.values()
    )
    out["issues"] = search(
        f"is:issue author:{account}{vis}", padded_start, padded_end, "created"
    )

    repos = sorted(
        {r.split("\t")[4] for r in out["prs"] + out["issues"]}
        | set(cfg["loc_repos"])
    )
    for repo in repos:
        try:
            if (
                gh("api", f"repos/{repo}", "--jq", ".private").strip()
                == "true"
            ):
                out["private"].append(repo)
        except RuntimeError:
            out["private"].append(repo)  # unreadable now: treat as private
    keep = repo_filter(a, out["private"])
    out["prs"] = [r for r in out["prs"] if keep(r.split("\t")[4])]
    out["issues"] = [r for r in out["issues"] if keep(r.split("\t")[4])]
    out["private"] = [r for r in out["private"] if keep(r)]

    loc_repos = [r for r in cfg["loc_repos"] if keep(r)]
    if not loc_repos:
        merged = collections.Counter(
            r.split("\t")[4] for r in out["prs"] if r.split("\t")[3]
        )
        loc_repos = [r for r, _ in merged.most_common(cfg["loc_repo_limit"])]
    for repo in loc_repos:
        try:
            rows = json.loads(
                gh(
                    "pr",
                    "list",
                    "-R",
                    repo,
                    "--author",
                    account,
                    "--state",
                    "merged",
                    "--limit",
                    "1000",
                    "--json",
                    "number,createdAt,mergedAt,additions,deletions,"
                    "changedFiles",
                )
            )
        except RuntimeError as e:
            print(f"  loc {repo} failed: {e}", flush=True)
            continue
        out["loc"][repo] = rows
        print(f"  loc {repo}: {len(rows)}", flush=True)
        time.sleep(5)

    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f)
    print(
        f"{a.out}: {len(out['prs'])} PRs, {len(out['issues'])} issues, "
        f"{len(out['private'])} private repos"
    )


if __name__ == "__main__":
    sys.exit(main())
