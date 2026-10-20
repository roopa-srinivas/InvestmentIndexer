import json

import numpy as np
import pandas as pd
import pytest

from indexer import export


def test_chart_and_table_agree_for_every_window(tmp_path):
    months = pd.period_range("1970-01", "2026-08", freq="M")
    rng = np.random.default_rng(1)
    returns = pd.DataFrame(rng.normal(0.008, 0.04, size=(len(months), 3)), index=months, columns=["market", "a", "b"])
    info = pd.DataFrame({"name": ["Market", "A", "B"], "group": ["Market", "Test", "Test"]}, index=["market", "a", "b"])
    rf = pd.Series(0.002, index=months)

    data = json.loads(export.write(returns, info, rf, path=tmp_path / "data.json").read_text())

    labels, paths = data["growth"]["labels"], data["growth"]["paths"]
    assert data["end"] == "2026-08" and labels[-1] == "2026-08"
    for years, window in data["windows"].items():
        base = labels.index(f"{2026 - int(years)}-08")
        for row in window["rows"]:
            chart_growth = paths[row["id"]][-1] / paths[row["id"]][base]
            assert chart_growth == pytest.approx(row["growth"], rel=1e-3)
