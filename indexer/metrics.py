"""Performance measures for a series of monthly decimal returns."""

import numpy as np
import pandas as pd

MONTHS_PER_YEAR = 12


def growth(returns):
    """What $1 grows to over the period."""
    return float((1 + returns).prod())


def cagr(returns):
    """Compound annual growth rate."""
    years = len(returns) / MONTHS_PER_YEAR
    return growth(returns) ** (1 / years) - 1


def volatility(returns):
    """Annualized standard deviation of monthly returns."""
    return float(returns.std(ddof=1) * np.sqrt(MONTHS_PER_YEAR))


def sharpe(returns, risk_free):
    """Annualized Sharpe ratio: average excess return per unit of risk."""
    excess = returns - risk_free.reindex(returns.index)
    sd = excess.std(ddof=1)
    return float(excess.mean() / sd * np.sqrt(MONTHS_PER_YEAR)) if sd > 0 else float("nan")


def max_drawdown(returns):
    """Largest peak-to-trough fall in value, as a negative fraction."""
    value = (1 + returns).cumprod()
    peak = value.cummax().clip(lower=1.0)  # the starting $1 counts as a peak
    return float((value / peak - 1).min())


def summarize(returns, risk_free):
    """All measures for one index over one window."""
    return {
        "cagr": cagr(returns),
        "volatility": volatility(returns),
        "sharpe": sharpe(returns, risk_free),
        "max_drawdown": max_drawdown(returns),
        "growth": growth(returns),
    }


def window(returns, end, years):
    """The `years` years of months ending at `end` (a monthly Period)."""
    start = end - (years * MONTHS_PER_YEAR - 1)
    return returns.loc[start:end]


def complete(frame):
    """Columns with no missing months in this window."""
    return frame.loc[:, frame.notna().all()]


def table(returns, risk_free, end, years):
    """One row per index with every measure, for indexes with full data."""
    frame = complete(window(returns, end, years))
    if len(frame) < years * MONTHS_PER_YEAR:
        raise ValueError(f"Not enough history for {years} years ending {end}.")
    return pd.DataFrame({col: summarize(frame[col], risk_free) for col in frame.columns}).T
