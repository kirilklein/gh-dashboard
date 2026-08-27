"""Regenerate holidays.json from the `holidays` package (maintainer-only; users need nothing).

Usage: pip install holidays && python3 tools/gen_holidays.py [--from 2024] [--to 2027]
"""
import argparse, datetime as dt, json, os, re

import holidays

D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    y = dt.date.today().year
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="y0", type=int, default=y - 2)
    ap.add_argument("--to", dest="y1", type=int, default=y + 1)
    a = ap.parse_args()
    years = range(a.y0, a.y1 + 1)
    out = {}
    for cls, code, *_ in holidays.registry.COUNTRIES.values():
        try:
            h = holidays.country_holidays(code, years=years)
        except Exception:
            continue
        out[code] = {"name": re.sub(r"(?<=[a-z])(?=[A-Z])", " ", cls),
                     "dates": sorted(d.isoformat() for d in h)}
    json.dump(out, open(f"{D}/holidays.json", "w"), separators=(",", ":"), sort_keys=True)
    print(f"{len(out)} countries, {sum(len(v['dates']) for v in out.values())} dates, "
          f"{a.y0}-{a.y1}")


if __name__ == "__main__":
    main()
