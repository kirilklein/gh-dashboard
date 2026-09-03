"""Packaged config.json defaults overlaid with ./config.local.json (git-ignored, personal)."""
import fnmatch, json, os

D = os.path.dirname(os.path.abspath(__file__))


def load_config(override=None):
    cfg = json.load(open(f"{D}/config.json"))
    local = override or "config.local.json"
    if os.path.exists(local):
        cfg.update(json.load(open(local)))
    return cfg


def add_repo_args(ap, cfg):
    ap.add_argument("--config", help="use this file instead of config.local.json")
    ap.add_argument("--public-only", action="store_true", default=cfg["public_only"],
                    help="drop activity in private repositories")
    ap.add_argument("--exclude-repo", action="append", default=list(cfg["exclude_repos"]),
                    metavar="OWNER/NAME", help="glob, repeatable, e.g. 'acme/*'")


def repo_filter(args, private):
    """Return keep(repo) honouring --public-only and --exclude-repo."""
    private = set(private)

    def keep(repo):
        if args.public_only and repo in private:
            return False
        return not any(fnmatch.fnmatch(repo, pat) for pat in args.exclude_repo)
    return keep
