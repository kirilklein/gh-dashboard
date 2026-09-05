"""Packaged config.json defaults overlaid with ./config.local.json (git-
ignored, personal)."""

import argparse
import fnmatch
import json
import os
from pathlib import Path

D = os.path.dirname(os.path.abspath(__file__))


def load_config(override=None):
    cfg = json.loads(Path(D, "config.json").read_text(encoding="utf-8"))
    local = override or "config.local.json"
    if override or os.path.exists(local):
        cfg.update(json.loads(Path(local).read_text(encoding="utf-8")))
    return cfg


def cli_config(argv):
    ap = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    ap.add_argument("--config")
    args, _ = ap.parse_known_args(argv)
    return load_config(args.config)


def add_repo_args(ap, cfg):
    ap.add_argument(
        "--config", help="use this file instead of config.local.json"
    )
    ap.add_argument(
        "--public-only",
        action="store_true",
        default=cfg["public_only"],
        help="drop activity in private repositories",
    )
    ap.add_argument(
        "--exclude-repo",
        action="append",
        default=list(cfg["exclude_repos"]),
        metavar="OWNER/NAME",
        help="glob, repeatable, e.g. 'acme/*'",
    )


def repo_filter(args, private):
    """Return keep(repo) honouring --public-only and --exclude-repo."""
    private = set(private)

    def keep(repo):
        if args.public_only and repo in private:
            return False
        return not any(fnmatch.fnmatch(repo, pat) for pat in args.exclude_repo)

    return keep
