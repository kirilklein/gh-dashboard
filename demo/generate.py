"""Generate a synthetic raw.json for a fictional account so the repo ships
with a demo.

Usage: python3 demo/generate.py [--out demo/raw.json] [--end 2026-08-27]
Deterministic (fixed seed). Nothing here comes from a real account.
"""

import argparse
import datetime as dt
import json
import os
import random

D = os.path.dirname(os.path.abspath(__file__))
ACCOUNT = "octodev"
REPOS = {
    "acme/api": 0.34,
    "acme/web": 0.26,
    "acme/infra": 0.15,
    "acme/data-pipeline": 0.12,
    "octodev/dotfiles": 0.05,
    "opensource/toolkit": 0.08,
}
HOLIDAYS = {"12-24", "12-25", "12-26", "12-31", "01-01"}
VACATION = [
    ("2026-02-16", "2026-02-20"),
    ("2026-07-06", "2026-07-24"),
    ("2025-10-13", "2025-10-17"),
]
WD_WEIGHT = [1.0, 1.15, 1.1, 1.05, 0.8, 0.06, 0.04]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=f"{D}/raw.json")
    ap.add_argument("--end", default="2026-08-27")
    ap.add_argument("--days", type=int, default=366)
    a = ap.parse_args()
    rnd = random.Random(7)
    end = dt.date.fromisoformat(a.end)
    start = end - dt.timedelta(a.days - 1)
    off = set()
    for s, e in VACATION:
        d = dt.date.fromisoformat(s)
        while d <= dt.date.fromisoformat(e):
            off.add(d)
            d += dt.timedelta(1)

    def iso(t):
        return t.strftime("%Y-%m-%dT%H:%M:%SZ")

    def work_time(day):
        # local 08:00-19:00 with a lunch dip; stored as UTC-1 (a
        # "Europe" flavoured account)
        h = rnd.choice(
            [8, 9, 9, 10, 10, 10, 11, 11, 13, 14, 14, 15, 15, 16, 16, 17, 18]
        )
        return dt.datetime.combine(
            day, dt.time(h - 1, rnd.randrange(60), rnd.randrange(60))
        )

    prs, issues, loc = [], [], {r: [] for r in REPOS}
    num = {r: rnd.randrange(200, 900) for r in REPOS}
    day = start - dt.timedelta(14)
    while day <= end:
        base = 1.6 * WD_WEIGHT[day.weekday()]
        if day.strftime("%m-%d") in HOLIDAYS or day in off:
            base *= 0.05
        season = 1 + 0.25 * (1 if 3 <= day.month <= 6 else -0.3)
        n = sum(1 for _ in range(6) if rnd.random() < base * season / 6)
        for _ in range(n):
            repo = rnd.choices(list(REPOS), weights=list(REPOS.values()))[0]
            merged = work_time(day)
            wait_h = (
                rnd.lognormvariate(4.6, 0.9)
                if rnd.random() < 0.12
                else rnd.lognormvariate(1.2, 1.3)
            )
            created = merged - dt.timedelta(hours=wait_h)
            if not (start <= merged.date() <= end):
                continue
            num[repo] += 1
            is_merged = rnd.random() < 0.9
            closed = merged
            prs.append(
                "\t".join(
                    [
                        str(num[repo]),
                        iso(created),
                        iso(closed),
                        iso(merged) if is_merged else "",
                        repo,
                    ]
                )
            )
            if is_merged:
                size = int(rnd.lognormvariate(4.3, 1.4))
                if rnd.random() < 0.015:
                    size = rnd.randrange(12000, 60000)
                add = int(size * rnd.uniform(0.45, 0.9))
                loc[repo].append(
                    {
                        "number": num[repo],
                        "createdAt": iso(created),
                        "mergedAt": iso(merged),
                        "additions": add,
                        "deletions": size - add,
                        "changedFiles": max(
                            1, int(size**0.55 * rnd.uniform(0.3, 1.2))
                        ),
                    }
                )
        for _ in range(3):
            if rnd.random() < base * 0.18:
                t = work_time(day)
                issues.append(
                    "\t".join(["0", iso(t), "", "", rnd.choice(list(REPOS))])
                )
        day += dt.timedelta(1)

    # Include unfinished work so the demo exercises backlog as well as
    # completed PRs.
    for i, repo in enumerate(REPOS):
        num[repo] += 1
        created = work_time(end - dt.timedelta(days=3 + i * 4))
        prs.append("\t".join([str(num[repo]), iso(created), "", "", repo]))

    out = {
        "account": ACCOUNT,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "prs": prs,
        "issues": issues,
        "loc": loc,
        "backlog_complete": True,
        "collected_at": iso(dt.datetime.combine(end, dt.time(23, 59, 59))),
        "private": [r for r in REPOS if r.startswith("acme/")],
    }
    json.dump(out, open(a.out, "w"))
    print(f"{a.out}: {len(prs)} PRs, {len(issues)} issues")


if __name__ == "__main__":
    main()
