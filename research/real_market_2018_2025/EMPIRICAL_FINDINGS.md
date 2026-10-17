# ATLAS | Empirical Findings & Risk Review

**Study status:** Reproduced by GitHub Actions on a pinned third-party historical archive. **Retrospective, exploratory—not evidence of trading alpha or institutional deployment.**

> Data classification: **PINNED THIRD-PARTY ARCHIVE — UNVERIFIED PRICE ADJUSTMENT.** The archive claims dividend/split-adjusted closes; that claim, vendor rights and total-return accuracy have not been independently audited.

## Research question

**When does diversification reduce downside, when does it fail, and how reliably can a risk engine detect tail risk?**

This study uses SPY, QQQ and TLT: **2,011 aligned closing-price observations / 2,010 daily returns**, 2018-01-02 to 2025-12-31. Three transparent, long-only rules rebalance every 21 sessions with an **assumed 8 bps one-way turnover cost**. SPY buy-and-hold is charged one initial 8 bps purchase cost.

![Empirical overview](../../docs/assets/atlas_research_snapshot.svg)

## 1 | Reviewed 2023–2025: return versus downside

**This period was previously examined and is not an untouched holdout.** Annual return is compounded CAGR. Expected shortfall below is historical one-day 95% tail loss.

| Allocation | CAGR | Annualized volatility | Maximum drawdown | Daily historical ES (95%) |
|---|---:|---:|---:|---:|
| SPY buy-and-hold, modeled initial cost | **23.00%** | 15.34% | -18.76% | 2.11% |
| 60% SPY / 40% TLT | 13.33% | **11.40%** | **-12.70%** | **1.57%** |
| Equal SPY / QQQ / TLT | 18.18% | 12.98% | -14.54% | 1.76% |
| 63-session inverse-volatility | 16.50% | 12.34% | -13.44% | 1.68% |

**Readout:** Lower downside risk came with lower realized return than SPY. No strategy demonstrated investment alpha in this comparison.

## 2 | Historical regime stress: hedges can fail

Ex-post date windows are selected with hindsight. These are *simulated* portfolio returns on archived historical closes, not desk executions.

| Window | Costed SPY | 60/40 SPY–TLT | Interpretation |
|---|---:|---:|---|
| COVID liquidity shock, Feb 19–Mar 23, 2020 | **-33.40%** | **-15.81%** | Duration exposure cushioned this simulated equity shock |
| Inflation / duration repricing, Jan 3–Oct 14, 2022 | **-23.83%** | **-27.13%** | Duration exposure worsened the simulated loss |

**Lesson:** The same hedge can protect in one macro regime and fail in another.

## 3 | Rolling 99% daily VaR: model calibration matters

Using **1,758 forecasts**, each built from only **252 prior sessions**, nominal 99% VaR implies **17.58 expected breaches**.

![VaR exception counts](../../docs/assets/atlas_var_backtest.svg)

| Portfolio | Model | Observed breaches | Kupiec coverage p | Christoffersen conditional coverage p |
|---|---|---:|---:|---:|
| SPY buy-and-hold | Historical simulation | 31 | 0.0037 | 0.0001 |
| SPY buy-and-hold | Gaussian EWMA | **42** | <0.0001 | <0.0001 |
| 60/40 | Historical simulation | 25 | 0.0944 | 0.0043 |
| 60/40 | Gaussian EWMA | **40** | <0.0001 | <0.0001 |

The elevated exceedance counts suggest risk underestimation under these historical assumptions, particularly for Gaussian EWMA. Tail-sample limitations mean these tests are *diagnostics*, not model certifications.

## 4 | Inference: exploratory, not confirmatory

Paired circular 21-session block bootstrap, 500 repetitions; outcome is **annualized arithmetic mean daily excess return**, not CAGR difference, relative to costed SPY.

| Allocation | Annualized mean excess | Exploratory 95% interval |
|---|---:|---|
| 60/40 | -8.72 percentage points | [-15.58, -1.14] pp |
| Equal thirds | -4.34 pp | [-9.55, +0.82] pp |
| Inverse volatility | -5.85 pp | [-12.41, +1.01] pp |

Multiple comparisons, regime drift, hindsight selection and already-reviewed outcomes prevent strong alpha claims.

## 5 | Verifiability and open methodology

- [Passed GitHub historical audit](https://github.com/yavuzaksoyy06-create/ATLAS-Cross-Asset-Trading-Risk-Research/actions/runs/39064709600) and generated aggregate research artifact.
- **48 reference metrics** numerically reconciled within **0.05 percentage points**; maximum recorded absolute difference: **0.0 pp at output precision**. This verifies computational agreement, not data vendor truth.
- [Pinned third-party public archive](https://github.com/revred/TradeSmart.Tracker), exact commit **7d9d769b0f2ddcedf4c1703cc979b865a37b580d**. The downloader checks Git blob hashes and locally records SHA256. Raw OHLCV is not redistributed here.
- Re-run commands: install dependencies using **python -m pip install -e '.[all]'**, then execute **python -m atlas.real_study --output results/real_market --repetitions 500**.
- Full Markdown research memo, HTML dashboard, performance, stress, cost, VaR and bootstrap reports are available as an [Actions artifact](https://github.com/yavuzaksoyy06-create/ATLAS-Cross-Asset-Trading-Risk-Research/actions/runs/39064709600) for the retention period.

### Persistent summary tables

Small aggregate tables are committed so the core findings remain reviewable after the GitHub Actions artifact expires: [performance](verified_performance_summary.csv) · [2020/2022 stress](verified_stress_summary.csv) · [99% VaR exceptions](verified_var_exceedances.csv) · [reference reconciliation](reference_reconciliation.json). These rounded review tables are extracted from the full archived audit; rerun the workflow for complete model and cost diagnostics.

### What this does *not* establish

No licensed-vendor total-return reconciliation; no actual bid/ask fills or order books; no financing, cash yield or taxes; no historical point-in-time ETF universe; no truly untouched confirmatory holdout, paper trading or live execution. SPY and QQQ overlap economically. Results from synthetic engineering fixtures are separated from this pinned historical-price analysis.

**Conclusion:** The defensible technical achievement is a reproducible, skeptical research workflow for comparing strategies and challenging risk models—not claims of superior predictive performance.
