"""Inline raw.json + config + holidays into template.html -> out/index.html.

Usage: python3 -m gh_dashboard.build [--raw raw.json] [--out out/index.html] [--anonymize-repos]
                                     [--public-only] [--exclude-repo GLOB ...] [--config FILE]

All aggregation happens in the page itself, so holidays, timezone and days off can be
changed in the browser without rebuilding. Only PR-level timestamps, sizes and repo names
are inlined; never titles, bodies or URLs.
"""
import argparse, datetime as dt, json, os

from .settings import add_repo_args, load_config, repo_filter

D = os.path.dirname(os.path.abspath(__file__))


def main(argv=None):
    cfg = load_config()
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="raw.json")
    ap.add_argument("--out", default="out/index.html")
    ap.add_argument("--anonymize-repos", action="store_true",
                    help="replace repository names with repo-1, repo-2, ...")
    add_repo_args(ap, cfg)
    a = ap.parse_args(argv)
    if a.config:
        cfg = load_config(a.config)
    raw = json.load(open(a.raw))
    keep = repo_filter(a, raw.get("private", []))

    loc = {(repo, pr["number"]): pr for repo, rows in raw["loc"].items() for pr in rows}
    repos, prs = [], []
    for line in raw["prs"]:
        num, created, closed, merged, repo = line.split("\t")
        if not keep(repo):
            continue
        if repo not in repos:
            repos.append(repo)
        l = loc.get((repo, int(num)))
        size = [l["additions"], l["deletions"], l["changedFiles"]] if l else None
        prs.append([created, closed, merged, repos.index(repo), size])
    loc_idx = [repos.index(r) for r in raw["loc"] if r in repos]
    if a.anonymize_repos:
        repos = [f"repo-{i + 1}" for i in range(len(repos))]

    data = {
        "account": raw["account"], "start": raw["start"], "end": raw["end"],
        "repos": repos, "prs": prs, "locRepos": loc_idx,
        "issues": [l.split("\t")[1] for l in raw["issues"] if keep(l.split("\t")[4])],
        "bigPr": cfg["big_pr"],
        "settings": {"country": cfg["country"], "timezone": cfg["timezone"],
                     "holidays": cfg["holidays"], "offDays": cfg["off_days"],
                     "events": cfg["events"]},
        "holidays": json.load(open(f"{D}/holidays.json")),
    }

    blob = json.dumps(data, separators=(",", ":"))
    fmt = lambda s: (lambda d: f"{d.day} {d:%b %Y}")(dt.date.fromisoformat(s))
    html = (open(f"{D}/template.html", encoding="utf-8").read()
            .replace("__DATA__", blob)
            .replace("__ACCOUNT__", data["account"])
            .replace("__RANGE__", f"{fmt(raw['start'])} - {fmt(raw['end'])}"))
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(html)
    print(f"wrote {a.out}: {len(prs)} PRs, {len(data['issues'])} issues, {len(repos)} repos")


if __name__ == "__main__":
    main()
