"""Ranking indexes, and checking whether past rankings predict future ones."""

import pandas as pd

from .metrics import MONTHS_PER_YEAR, table, window, complete, cagr

# Higher is better for all of these except drawdown and volatility, where
# "better" means a smaller loss or less risk.
ASCENDING = {"cagr": False, "sharpe": False, "growth": False, "max_drawdown": False, "volatility": True}


def rank(returns, info, risk_free, end, years, by="cagr"):
    """Every index with full data, best first by `by`, with its rank."""
    if by not in ASCENDING:
        raise ValueError(f"by must be one of: {', '.join(ASCENDING)}")
    scores = table(returns, risk_free, end, years).join(info)
    scores = scores.sort_values(by, ascending=ASCENDING[by])
    scores.insert(0, "rank", range(1, len(scores) + 1))
    return scores


def persistence(returns, end, years):
    """Do the best indexes of one period stay the best in the next?

    Ranks every index by CAGR over the `years` before `end` and over the
    `years` before that, and returns the Spearman rank correlation between
    the two (1 = same order, 0 = no relation, -1 = reversed), plus how many
    of the earlier top 10 were still in the top 10.
    """
    span = years * MONTHS_PER_YEAR
    recent = complete(window(returns, end, years))
    earlier = complete(window(returns, end - span, years))
    both = recent.columns.intersection(earlier.columns)
    recent_cagr = recent[both].apply(cagr)
    earlier_cagr = earlier[both].apply(cagr)
    top_then = set(earlier_cagr.nlargest(10).index)
    top_now = set(recent_cagr.nlargest(10).index)
    return {
        "earlier": f"{end - 2 * span + 1} to {end - span}",
        "recent": f"{end - span + 1} to {end}",
        "indexes": len(both),
        "spearman": float(earlier_cagr.rank().corr(recent_cagr.rank())),
        "top10_repeat": len(top_then & top_now),
    }
