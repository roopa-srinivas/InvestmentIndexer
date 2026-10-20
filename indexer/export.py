"""Writes everything the web report shows to site/data.json.

All the math happens here in pandas; the page only displays the results.
"""

import json
import math
from pathlib import Path

from .metrics import MONTHS_PER_YEAR
from .ranking import persistence, rank

WINDOWS = [1, 3, 5, 10, 15, 20, 30, 50]
OUT = Path(__file__).resolve().parent.parent / "site" / "data.json"


def _clean(value, digits=4):
    return None if value is None or (isinstance(value, float) and math.isnan(value)) else round(float(value), digits)


def write(returns, info, risk_free, path=OUT):
    end = returns.dropna(how="all").index[-1]
    windows = {}
    for years in WINDOWS:
        scores = rank(returns, info, risk_free, end, years, by="cagr")
        windows[years] = {
            "start": str(end - (years * MONTHS_PER_YEAR - 1)),
            "rows": [
                {
                    "id": index_id,
                    "cagr": _clean(row["cagr"]),
                    "volatility": _clean(row["volatility"]),
                    "sharpe": _clean(row["sharpe"], 3),
                    "max_drawdown": _clean(row["max_drawdown"]),
                    "growth": _clean(row["growth"], 3),
                }
                for index_id, row in scores.iterrows()
            ],
        }

    # Growth of $1 over the longest window, one point a year in the same
    # month as `end`, so every window's start lines up with a point and the
    # chart's end value matches the table exactly. The first point is the
    # month before the window, when the $1 goes in.
    longest = max(WINDOWS)
    start = end - (longest * MONTHS_PER_YEAR - 1)
    values = (1 + returns.loc[start:end]).cumprod()
    points = [start - 1] + [p for p in values.index if p.month == end.month]
    paths = {col: [1.0] + [_clean(values.at[p, col], 4) for p in points[1:]] for col in values.columns}

    data = {
        "end": str(end),
        "windows": windows,
        "indexes": [{"id": i, **row} for i, row in info.iterrows()],
        "growth": {"labels": [str(p) for p in points], "paths": paths},
        "persistence": {str(y): persistence(returns, end, y) for y in (10, 15, 20)},
        "source": "Kenneth R. French Data Library, value-weighted monthly returns",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, separators=(",", ":")))
    return path
