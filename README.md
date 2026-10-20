# Investment Indexer

Which corners of the US stock market actually grew the most? This tool ranks **125 market indexes** (49 industries, plus portfolios sorted by size, value, momentum, profitability and investment) by growth, risk and worst losses over any window, using Python and pandas. **Rebuilt in 2026.**

**Live report:** https://roopa-srinivas.github.io/InvestmentIndexer/

## What it finds (15 years to August 2026)
- **Best:** Electronic Equipment, 26.6% a year ($1 → $34.38). **Worst:** Coal, −6.7% a year ($1 → $0.35).
- **The total market ranked #35 of 125**, growing 15.0% a year; only 34 indexes beat it.
- **Winners rarely repeat:** none of the top 10 from 1996–2011 made the top 10 in 2011–2026, and the rank correlation between the two periods is 0.10.

## Usage
```sh
pip install -r requirements.txt
python -m indexer rank --years 15 --top 10                # best and worst 10
python -m indexer rank --years 20 --by sharpe --group Industry
python -m indexer rank --years 10 --end 2008-12           # any past window
python -m indexer export                                  # rebuild site/data.json for the report
pytest
```
`--by` accepts `cagr`, `sharpe`, `max_drawdown`, `volatility` or `growth`. Data is downloaded once and cached in `data/raw/`.

## How it works
| Step | Code |
|---|---|
| Download each zipped CSV from the [Kenneth R. French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html) and parse its first table (value-weighted monthly returns), turning the `-99.99` and `-999` markers into missing values | `indexer/french.py` |
| Pick 125 indexes from 8 files and give them readable names and groups | `indexer/universe.py` |
| Compute CAGR, annualized volatility, Sharpe ratio (against the risk-free rate), maximum drawdown and growth of $1 for any window. Indexes missing a month in the window are left out of it | `indexer/metrics.py` |
| Rank by any measure, and compare rankings in back-to-back windows with a Spearman correlation | `indexer/ranking.py` |
| Export the results for the web report, which only displays them | `indexer/export.py`, `index.html`, `site/` |

## Notes
- Returns include dividends and are before fees and taxes. These are research portfolios built from CRSP data, not funds you can buy directly. This is for learning, not investment advice.
- Data: Kenneth R. French Data Library, Tuck School of Business at Dartmouth.
