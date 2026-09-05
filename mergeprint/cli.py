"""One command: a few questions (Enter keeps the default), then fetch, build and open.

Usage: mergeprint [--yes] [--no-open]
Files land in the current directory: raw.json, config.local.json, out/index.html.
Timezone, country, days off and events can also be changed later inside the page.
"""
import argparse, json, locale, os, shutil, subprocess, sys, webbrowser

from . import build, collect
from .settings import load_config

LOCAL = "config.local.json"


def ask(label, default=""):
    shown = f" [{default}]" if default else ""
    return input(f"{label}{shown}: ").strip() or default


def yes_no(label, default):
    ans = input(f"{label} [{'Y/n' if default else 'y/N'}]: ").strip().lower()
    return default if not ans else ans.startswith("y")


def system_timezone():
    if os.environ.get("TZ"):
        return os.environ["TZ"]
    try:
        return os.readlink("/etc/localtime").split("zoneinfo/", 1)[1]
    except (OSError, IndexError):
        return ""


def system_country():
    loc = locale.getlocale()[0] or ""
    return loc.split("_")[-1][:2].upper() if "_" in loc else ""


def gh_login():
    if not shutil.which("gh"):
        sys.exit("gh CLI not found. Install it from https://cli.github.com/ then run: gh auth login")
    r = subprocess.run(["gh", "api", "user", "--jq", ".login"], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("gh is not logged in. Run: gh auth login")
    return r.stdout.strip()


def main(argv=None):
    ap = argparse.ArgumentParser(description="Your year on GitHub, one page, built locally.")
    ap.add_argument("--yes", "-y", action="store_true", help="accept all defaults, no prompts")
    ap.add_argument("--no-open", action="store_true", help="do not open the result in a browser")
    a = ap.parse_args(argv)

    cfg = load_config()
    first_run = not os.path.exists(LOCAL)
    answers = {
        "account": cfg["account"] or gh_login(),
        "days": cfg["days"],
        "public_only": True if first_run else cfg["public_only"],
        "exclude_repos": cfg["exclude_repos"],
        "timezone": cfg["timezone"] or system_timezone(),
        "country": cfg["country"] or system_country(),
    }
    if not a.yes:
        print("mergeprint: Enter keeps the default in brackets.\n")
        answers["account"] = ask("GitHub account", answers["account"])
        answers["days"] = int(ask("Days to cover", str(answers["days"])))
        answers["public_only"] = yes_no("Public repositories only (private activity never touches disk)",
                                        answers["public_only"])
        ex = ask("Repositories to exclude, comma-separated globs like acme/*",
                 ",".join(answers["exclude_repos"]))
        answers["exclude_repos"] = [g.strip() for g in ex.split(",") if g.strip()]
        answers["timezone"] = ask("Timezone (IANA name)", answers["timezone"])
        answers["country"] = ask("Country code for public holidays", answers["country"]).upper()
        print("\nDays off and events are added later in the page's Settings drawer.")

    local = json.load(open(LOCAL)) if not first_run else {}
    local.update(answers)
    json.dump(local, open(LOCAL, "w"), indent=1)

    repo_args = ["--public-only"] if answers["public_only"] else []
    for g in answers["exclude_repos"]:
        repo_args += ["--exclude-repo", g]
    print(f"\nFetching {answers['days']} days for {answers['account']}. "
          "A few minutes: the collector paces itself under GitHub's rate limit.\n")
    collect.main(["--account", answers["account"], "--days", str(answers["days"])] + repo_args)
    build.main(["--out", "out/index.html"] + repo_args)
    path = os.path.abspath("out/index.html")
    print(f"\nDone: {path}\nSettings saved in {LOCAL}. Share the page deliberately: send the file, or publish.sh in the repo pushes it to gh-pages.")
    if not a.no_open:
        webbrowser.open(f"file://{path}")


if __name__ == "__main__":
    main()
