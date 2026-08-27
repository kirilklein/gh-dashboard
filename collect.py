"""Fetch a rolling year of GitHub activity for one account into raw.json.

Usage: python3 collect.py [--account NAME] [--end YYYY-MM-DD] [--days 366]
                          [--public-only] [--exclude-repo GLOB ...] [--out raw.json]

Uses the `gh` CLI and whatever account it is logged in as. Nothing is sent anywhere
else; raw.json stays on disk and is git-ignored. With --public-only the search itself is
restricted to public repositories, so private activity never reaches the disk.
"""
import argparse, collections, datetime as dt, json, os, subprocess, sys, time

from settings import add_repo_args, load_config, repo_filter

D = os.path.dirname(os.path.abspath(__file__))
JQ = ('.items[] | [.number, .created_at, (.closed_at//""), (.pull_request.merged_at//""), '
      '(.repository_url|sub("https://api.github.com/repos/";""))] | @tsv')


def gh(*args):
    r = subprocess.run(["gh", *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[:200])
    return r.stdout


def search(q):
    """Paged issue search, paced to stay under GitHub's 30/min secondary limit."""
    rows, page = [], 1
    while page <= 12:
        try:
            out = gh("api", "-X", "GET", "search/issues", "-f", f"q={q}",
                     "-f", "per_page=100", "-f", f"page={page}", "--jq", JQ)
        except RuntimeError as e:
            print(f"  retry p{page}: {e}", flush=True)
            time.sleep(45)
            continue
        lines = [l for l in out.splitlines() if l.strip()]
        rows += lines
        print(f"  {q} p{page}: {len(lines)}", flush=True)
        time.sleep(3)
        if len(lines) < 100:
            break
        page += 1
    return rows


def months(start, end):
    out, y, m = [], start.year, start.month
    while (y, m) <= (end.year, end.month):
        out.append(f"{y}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def main():
    cfg = load_config()
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", default=cfg["account"])
    ap.add_argument("--end", default=dt.date.today().isoformat())
    ap.add_argument("--days", type=int, default=cfg["days"])
    ap.add_argument("--out", default=f"{D}/raw.json")
    add_repo_args(ap, cfg)
    a = ap.parse_args()
    if a.config:
        cfg = load_config(a.config)
    account = a.account or gh("api", "user", "--jq", ".login").strip()
    end = dt.date.fromisoformat(a.end)
    start = end - dt.timedelta(a.days - 1)
    vis = " is:public" if a.public_only else ""
    print(f"account {account}, {start} .. {end}{vis}")

    out = {"account": account, "start": start.isoformat(), "end": end.isoformat(),
           "prs": [], "issues": [], "loc": {}, "private": []}
    for m in months(start, end):
        out["prs"] += search(f"is:pr author:{account} is:closed closed:{m}{vis}")
        out["issues"] += search(f"is:issue author:{account} created:{m}{vis}")

    repos = sorted({r.split("\t")[4] for r in out["prs"] + out["issues"]})
    for repo in repos:
        try:
            if gh("api", f"repos/{repo}", "--jq", ".private").strip() == "true":
                out["private"].append(repo)
        except RuntimeError:
            out["private"].append(repo)   # unreadable now: treat as private
    keep = repo_filter(a, out["private"])
    out["prs"] = [r for r in out["prs"] if keep(r.split("\t")[4])]
    out["issues"] = [r for r in out["issues"] if keep(r.split("\t")[4])]

    loc_repos = [r for r in cfg["loc_repos"] if keep(r)]
    if not loc_repos:
        merged = collections.Counter(r.split("\t")[4] for r in out["prs"] if r.split("\t")[3])
        loc_repos = [r for r, _ in merged.most_common(cfg["loc_repo_limit"])]
    for repo in loc_repos:
        try:
            rows = json.loads(gh("pr", "list", "-R", repo, "--author", account, "--state", "merged",
                                 "--limit", "1000", "--json",
                                 "number,createdAt,mergedAt,additions,deletions,changedFiles"))
        except RuntimeError as e:
            print(f"  loc {repo} failed: {e}", flush=True)
            continue
        out["loc"][repo] = rows
        print(f"  loc {repo}: {len(rows)}", flush=True)
        time.sleep(5)

    json.dump(out, open(a.out, "w"))
    print(f"{a.out}: {len(out['prs'])} PRs, {len(out['issues'])} issues, "
          f"{len(out['private'])} private repos")


if __name__ == "__main__":
    sys.exit(main())
