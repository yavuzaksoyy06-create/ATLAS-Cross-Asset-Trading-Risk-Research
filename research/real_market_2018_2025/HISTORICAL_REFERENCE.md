# Archived ETF data | Historical reference calculation

**Evidence status:** The reference computation used observed third-party archived ETF prices read via GitHub in a separate evaluator. The historical data downloader in Python was **not executed** inside the offline build environment. Do **not** confuse the reference values below with the institutional cost-matched empirical audit, which is generated when users run `python -m atlas.real_study` with network access.

## Data lineage

- Source: [revred/TradeSmart.Tracker](https://github.com/revred/TradeSmart.Tracker); pinned commit `7d9d769b0f2ddcedf4c1703cc979b865a37b580d`.
- Raw files: `market/us/spy.csv`, `market/us/qqq.csv`, `market/us/tlt.csv` (not included).
- Source's own README declares data sourced primarily from Stooq and otherwise Yahoo, and describes `Close` as adjusted for dividends and splits; no independent verification performed.
- Historical price window: 2018-01-02 through 2025-12-31, **2,011 aligned trading sessions** (2,010 close-to-close returns).
- Reviewed chronological segment: 2023-01-03 through 2025-12-31, **752 returns**; **not a pristine out-of-sample holdout**.
- Every archive file is pinned to an exact Git blob SHA1; expected hashes are in [`REFERENCE_RESULTS.json`](REFERENCE_RESULTS.json). Source rights are not independently verified.

## Results (original retrospective uncosted-benchmark evaluator)

| Strategy | CAGR | Annualized volatility | Max drawdown | Daily 95% VaR loss |
|---|---:|---:|---:|---:|
| Passive SPY (zero cost) | 23.00% | 15.34% | -18.76% | 1.42% |
| 60% SPY / 40% TLT | 13.33% | 11.40% | -12.70% | 1.09% |
| Equal SPY / QQQ / TLT | 18.18% | 12.98% | -14.54% | 1.25% |
| Inverse-volatility 63d | 16.50% | 12.34% | -13.44% | 1.20% |

The plain SPY benchmark excluded trading fees. The portfolios use a **21-session rebalance** with **8 bps per unit of absolute one-way turnover** (a modeled 3 bps commission + 5 bps slippage). A lower portfolio drawdown need not imply superior investment performance: SPY had the highest CAGR during this inspected period and materially larger downside drawdown.

## How the institutional audit improves the older reference

The new [`institutional_report.py`](../../src/atlas/institutional_report.py) analyzes the same pinned source through Python using an additional **costed passive SPY buy-and-hold** benchmark, 0–30 bps cost sensitivities, 2020/2022 historical realized-event replay, rolling 99% historical and Gaussian EWMA VaR validation, Kupiec and Christoffersen diagnostics, and paired block-bootstrap intervals of arithmetic daily mean excess. It writes English `EMPIRICAL_RESEARCH_MEMO.md`, CSV analyses and an interactive dashboard after the downloader succeeds.

Results from those new tests are **not prefilled with invented numbers**. Running the pinned downloader is required to produce them.

## What cannot be concluded

- That ATLAS earned a live or simulated trading-account profit, exceeded a market index after fees, or had verified predictive alpha.
- That an adjusted-close price is a historical executable quote or that dividends/rights were independently reconciled.
- That the 2023–2025 segment is a genuinely untouched prospective test set. All results above are retrospective.
- That the analysis satisfies a trading desk's market risk regulatory, financing, liquidity or execution standards.

This report is *research evidence with explicit limitations*, not investment advice.
