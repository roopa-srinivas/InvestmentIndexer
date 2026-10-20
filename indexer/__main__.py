"""Command line:

    python -m indexer rank [--years 15] [--by cagr] [--top 10] [--group Industry] [--end 2026-08]
    python -m indexer export        # writes site/data.json for the web report
"""

import argparse
import sys

import pandas as pd

from . import export
from .ranking import ASCENDING, persistence, rank
from .universe import load

CACHE = "data/raw"


def _percent(x):
    return f"{x * 100:6.1f}%"


def print_ranking(scores, top, by):
    shown = pd.concat([scores.head(top), scores.tail(top)]) if len(scores) > 2 * top else scores
    print(f"{'#':>4}  {'Index':<34} {'Group':<14} {'CAGR':>7} {'Vol':>7} {'Sharpe':>6} {'Max DD':>7} {'$1 →':>8}")
    previous = None
    for index_id, row in shown.iterrows():
        if previous is not None and row["rank"] != previous + 1:
            print(f"{'…':>4}")
        previous = row["rank"]
        print(
            f"{row['rank']:>4}  {row['name'][:34]:<34} {row['group'][:14]:<14} {_percent(row['cagr'])} "
            f"{_percent(row['volatility'])} {row['sharpe']:>6.2f} {_percent(row['max_drawdown'])} {row['growth']:>8.2f}"
        )


def main(argv=None):
    parser = argparse.ArgumentParser(prog="indexer", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    r = sub.add_parser("rank", help="rank indexes over a window")
    r.add_argument("--years", type=int, default=15)
    r.add_argument("--by", choices=sorted(ASCENDING), default="cagr")
    r.add_argument("--top", type=int, default=10, help="show the top and bottom N")
    r.add_argument("--group", help="only one group, e.g. Industry, Size, Value, Momentum")
    r.add_argument("--end", help="last month of the window, YYYY-MM (default: latest)")
    sub.add_parser("export", help="write site/data.json")
    args = parser.parse_args(argv)

    returns, info, risk_free = load(CACHE)
    if args.command == "export":
        path = export.write(returns, info, risk_free)
        print(f"wrote {path}")
        return 0

    end = pd.Period(args.end, freq="M") if args.end else returns.dropna(how="all").index[-1]
    if args.group:
        keep = info.index[info["group"].str.lower() == args.group.lower()]
        if keep.empty:
            parser.error(f"no group called {args.group!r}; groups are: {', '.join(info['group'].unique())}")
        returns = returns[keep]
    scores = rank(returns, info, risk_free, end, args.years, by=args.by)
    start = end - (args.years * 12 - 1)
    print(f"{len(scores)} indexes ranked by {args.by}, {start} to {end}\n")
    print_ranking(scores, args.top, args.by)
    p = persistence(returns, end, args.years)
    print(
        f"\nDid the winners repeat? Comparing {p['earlier']} with {p['recent']}: "
        f"rank correlation {p['spearman']:.2f}, {p['top10_repeat']} of the earlier top 10 stayed in the top 10."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
