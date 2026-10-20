import pandas as pd
import pytest

from indexer.ranking import persistence, rank
from indexer.universe import _grid_name

MONTHS = pd.period_range("2000-01", periods=48, freq="M")
END = MONTHS[-1]


def frame(columns):
    return pd.DataFrame(columns, index=MONTHS)


def info(ids):
    return pd.DataFrame({"name": ids, "group": "Test"}, index=ids)


def test_rank_orders_best_first_and_numbers_them():
    returns = frame({"slow": [0.001] * 48, "fast": [0.02] * 48, "mid": [0.01] * 48})
    rf = pd.Series(0.0, index=MONTHS)
    scores = rank(returns, info(list(returns)), rf, END, 2)
    assert list(scores.index) == ["fast", "mid", "slow"]
    assert list(scores["rank"]) == [1, 2, 3]


def test_volatility_ranks_calmest_first():
    returns = frame({"calm": [0.01, 0.012] * 24, "wild": [0.10, -0.08] * 24})
    rf = pd.Series(0.0, index=MONTHS)
    assert rank(returns, info(list(returns)), rf, END, 2, by="volatility").index[0] == "calm"


def test_unknown_measure_is_rejected():
    returns = frame({"a": [0.01] * 48})
    with pytest.raises(ValueError):
        rank(returns, info(["a"]), pd.Series(0.0, index=MONTHS), END, 2, by="luck")


def test_persistence_detects_a_complete_reversal():
    # Each index does well in the first two years and badly in the next two,
    # in exactly the opposite order.
    cols = {f"i{n}": [0.001 * n] * 24 + [0.001 * (12 - n)] * 24 for n in range(1, 12)}
    p = persistence(frame(cols), END, 2)
    assert p["spearman"] == pytest.approx(-1.0)
    assert p["indexes"] == 11
    assert p["top10_repeat"] == 9  # 11 indexes: the top 10 sets overlap in 9


def test_size_value_grid_names():
    assert _grid_name("SMALL LoBM") == (1, 1, "Smallest growth")
    assert _grid_name("ME3 BM2") == (3, 2, "Mid growth-leaning")
    assert _grid_name("BIG HiBM") == (5, 5, "Largest value")
