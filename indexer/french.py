"""Downloads and parses files from the Kenneth R. French Data Library.

Each file is a zipped CSV holding several tables one after another (value
weighted monthly, equal weighted monthly, annual, ...). We only want the
first one: value-weighted monthly returns, in percent, one row per YYYYMM.
"""

import io
import re
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

BASE_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
DATA_ROW = re.compile(r"^\s*(\d{6})\s*,")
MISSING = (-99.99, -999.0)


def download(name, cache_dir):
    """The file's CSV text, from cache_dir if already downloaded."""
    cache = Path(cache_dir) / f"{name}.csv"
    if not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(f"{BASE_URL}{name}_CSV.zip", timeout=60) as response:
            archive = zipfile.ZipFile(io.BytesIO(response.read()))
        cache.write_bytes(archive.read(archive.namelist()[0]))
    return cache.read_text(encoding="latin-1")


def first_monthly_table(text):
    """The first table in a French CSV as a DataFrame of decimal returns,
    indexed by month (a pandas Period). Missing values become NaN."""
    header, rows = None, []
    for line in text.splitlines():
        if header is None:
            if line.startswith(","):
                header = [h.strip() for h in line.split(",")[1:]]
            continue
        if not DATA_ROW.match(line):
            if rows:
                break  # the next table starts here
            continue
        cells = [c.strip() for c in line.split(",")]
        rows.append([cells[0]] + [float(c) for c in cells[1 : len(header) + 1]])
    if header is None or not rows:
        raise ValueError("No monthly table found.")
    frame = pd.DataFrame(rows, columns=["month"] + header)
    frame["month"] = pd.PeriodIndex(frame["month"], freq="M")
    frame = frame.set_index("month")
    frame = frame.replace(list(MISSING), np.nan)
    return frame / 100.0
