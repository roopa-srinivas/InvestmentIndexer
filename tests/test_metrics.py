import numpy as np
import pandas as pd
import pytest

from indexer import metrics


def monthly(values, start="2000-01"):
    return pd.Series(values, index=pd.period_range(start, periods=len(values), freq="M"))


def test_steady_one_percent_a_month():
    r = monthly([0.01] * 24)
    assert metrics.growth(r) == pytest.approx(1.01**24)
    assert metrics.cagr(r) == pytest.approx(1.01**12 - 1)
    assert metrics.volatility(r) == pytest.approx(0)
    assert metrics.max_drawdown(r) == 0


def test_drawdown_peak_to_trough():
    # $1 -> 1.5 -> 0.75 -> 1.125: worst fall is 50% from the 1.5 peak.
    r = monthly([0.5, -0.5, 0.5])
    assert metrics.max_drawdown(r) == pytest.approx(-0.5)


def test_drawdown_counts_an_immediate_loss():
    assert metrics.max_drawdown(monthly([-0.2, 0.1])) == pytest.approx(-0.2)


def test_sharpe_is_excess_return_over_risk():
    r = monthly([0.02, 0.00] * 6)
    rf = monthly([0.005] * 12)
    excess = r - rf
    expected = excess.mean() / excess.std(ddof=1) * np.sqrt(12)
    assert metrics.sharpe(r, rf) == pytest.approx(expected)


def test_window_is_exactly_n_years_ending_at_end():
    r = monthly([0.01] * 60)
    w = metrics.window(r, pd.Period("2004-12", freq="M"), 2)
    assert len(w) == 24
    assert str(w.index[0]) == "2003-01" and str(w.index[-1]) == "2004-12"


def test_table_skips_indexes_with_gaps_and_refuses_short_history():
    frame = pd.DataFrame({"full": [0.01] * 24, "gappy": [0.01] * 23 + [np.nan]}, index=pd.period_range("2000-01", periods=24, freq="M"))
    rf = monthly([0.0] * 24)
    t = metrics.table(frame, rf, pd.Period("2001-12", freq="M"), 2)
    assert list(t.index) == ["full"]
    with pytest.raises(ValueError):
        metrics.table(frame, rf, pd.Period("2001-12", freq="M"), 3)
