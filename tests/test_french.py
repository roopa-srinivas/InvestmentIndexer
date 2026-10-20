import math

import pandas as pd
import pytest

from indexer.french import first_monthly_table

SAMPLE = """This file was created using the 202608 CRSP database.
Missing data are indicated by -99.99 or -999.

  Average Value Weighted Returns -- Monthly
,Agric,Food ,Soda
192607,   2.37,   0.12, -99.99
192608,   2.23,   2.68,   1.50
192609,  -0.57,   1.58,  -999

  Average Equal Weighted Returns -- Monthly
,Agric,Food ,Soda
192607,  50.00,  50.00,  50.00
"""


def test_reads_only_the_first_table_as_decimals():
    table = first_monthly_table(SAMPLE)
    assert list(table.columns) == ["Agric", "Food", "Soda"]
    assert len(table) == 3
    assert table.loc[pd.Period("1926-08", freq="M"), "Food"] == pytest.approx(0.0268)


def test_missing_markers_become_nan():
    table = first_monthly_table(SAMPLE)
    assert math.isnan(table.loc[pd.Period("1926-07", freq="M"), "Soda"])
    assert math.isnan(table.loc[pd.Period("1926-09", freq="M"), "Soda"])


def test_no_table_is_an_error():
    with pytest.raises(ValueError):
        first_monthly_table("just a note\n")
