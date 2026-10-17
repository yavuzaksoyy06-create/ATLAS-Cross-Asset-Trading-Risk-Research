<div align="center">

# ATLAS
### Cross-Asset Trading & Risk Intelligence

**Research the trade. Quantify the downside. Challenge the risk model.**

A reproducible Python research platform that connects **portfolio construction, cost-aware backtesting, historical stress analysis, Value-at-Risk validation, and simulated trading-desk risk decisions**.

[![Quant Research CI](https://github.com/yavuzaksoyy06-create/ATLAS-Cross-Asset-Trading-Risk-Research/actions/workflows/tests.yml/badge.svg)](https://github.com/yavuzaksoyy06-create/ATLAS-Cross-Asset-Trading-Risk-Research/actions/workflows/tests.yml)
[![Pinned ETF Audit](https://github.com/yavuzaksoyy06-create/ATLAS-Cross-Asset-Trading-Risk-Research/actions/workflows/pinned-market-audit.yml/badge.svg)](https://github.com/yavuzaksoyy06-create/ATLAS-Cross-Asset-Trading-Risk-Research/actions/workflows/pinned-market-audit.yml)
![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-2B6079)
![Type](https://img.shields.io/badge/Project-Independent%20Quant%20Research-264566)

[**Empirical findings**](research/real_market_2018_2025/EMPIRICAL_FINDINGS.md) · [**Research methodology**](docs/RESEARCH_METHODOLOGY.md) · [**Model risks**](docs/MODEL_RISK_REGISTER.md) · [**Reproduce it**](docs/REPRODUCIBILITY.md) · [**Interview brief**](docs/RECRUITER_BRIEF.md)

</div>

![ATLAS: historical trading and risk research highlights](docs/assets/atlas_research_snapshot.svg)

> **What ATLAS is:** An educational, independently developed quantitative-finance engineering and research system. **What it is not:** a live trading system, a validated source of alpha, a licensed market-data product, or a platform affiliated with a financial institution. Historical prices come from a **commit-pinned third-party ETF archive; price adjustments remain independently unverified**.

## The question behind ATLAS

**How should a trading or risk analyst evaluate an allocation idea when market regimes change, turnover costs matter, and the risk model itself may be wrong?**

ATLAS connects the complete research chain:

**Historical data → source-integrity checks → past-only decisions → cost-aware portfolio returns → stress windows → VaR backtests → uncertainty analysis → reproducible report.**

Instead of selecting the best-looking backtest and stopping there, the research deliberately includes *underperformance*, failed hedges and VaR calibration problems.

## Evidence: 2018–2025 ETF research

|  | Evidence |
|---|---|
| Market instruments | **SPY · QQQ · TLT** (equity / Nasdaq equity / long US Treasury ETF proxies) |
| Observations | **2,011 aligned daily closes; 2,010 return sessions** |
| Date span | **2018-01-02 – 2025-12-31** |
| Rules tested | **60/40 · equal thirds · 63-session inverse volatility**, compared with costed passive SPY |
| Implementation | Long-only; rebalance every **21 sessions**; **8 bps assumed one-way turnover cost** |
| Audit | [GitHub Actions successful historical run](https://github.com/yavuzaksoyy06-create/ATLAS-Cross-Asset-Trading-Risk-Research/actions/runs/39064709600), **48 numerically reconciled metrics** |

### 2023–2025: lower drawdown did not mean higher return

| Allocation | CAGR | Volatility | Max drawdown |
|---|---:|---:|---:|
| **SPY, buy-and-hold with initial modeled cost** | **23.00%** | 15.34% | -18.76% |
| 60% SPY / 40% TLT | 13.33% | **11.40%** | **-12.70%** |
| Equal thirds (SPY / QQQ / TLT) | 18.18% | 12.98% | -14.54% |
| 63-session inverse volatility | 16.50% | 12.34% | -13.44% |

**Finding:** In this reviewed period, diversification reduced the simulated drawdown, but the tested diversified strategies underperformed passive SPY on CAGR. **The 2023–2025 segment was examined previously, and is not an untouched out-of-sample validation set.**

### Two regimes, opposite lessons

| Historical stress replay | Costed SPY | 60/40 allocation | Interpretation |
|---|---:|---:|---|
| **2020 COVID liquidity shock** | -33.40% | -15.81% | Duration exposure cushioned losses |
| **2022 inflation / duration repricing** | -23.83% | -27.13% | Duration exposure made losses worse |

**The insight is the change in the hedge—not a claim that the allocation always works.**

### Risk engine: 99% VaR is a hypothesis to test

![Observed vs expected VaR breaches](docs/assets/atlas_var_backtest.svg)

Over **1,758 one-day risk forecasts**, a correctly calibrated 99% VaR model targets **about 17.6 breaches**. For SPY the **historical simulation recorded 31 breaches** and **Gaussian EWMA recorded 42**. The empirical shortfall highlights the importance of model governance and exception monitoring. These are educational diagnostics, not regulatory validation.

**[Read the complete empirical findings →](research/real_market_2018_2025/EMPIRICAL_FINDINGS.md)**

## What is implemented

| Research / system layer | Components |
|---|---|
| **Data governance** | Source-commit pinning, Git blob verification, SHA256 provenance, strict separation of historical and synthetic inputs |
| **Allocation engines** | Fixed/equal allocations, inverse volatility, momentum, CVaR and heuristic regime research |
| **Portfolio accounting** | Historical rebalancing, capital-weight drift, cost/slippage assumptions, benchmark alignment |
| **Downside risk** | Drawdown, historical VaR, expected shortfall, rolling 99% historical and Gaussian EWMA forecasts |
| **Validation & inference** | Kupiec and Christoffersen coverage tests, past-only decisions, paired moving-block bootstrap, cost sensitivity |
| **Market stress** | Ex-post historical event windows and explicitly separate hypothetical shock scenarios |
| **Trading-desk prototype** | Illustrative quote/RFQ logic and pre-trade portfolio risk-limit gate—not actual order routing |
| **Machine learning appendix** | Optional purged walk-forward classification, Brier-score evaluation against a naive base-rate |
| **Engineering** | Python package and CLI, Streamlit UI, automated tests on Python 3.11/3.12/3.13, GitHub Actions research audit |

### Research workflow

~~~mermaid
flowchart LR
    A[Historical archive or labeled fixture] --> B[Provenance and quality gates]
    B --> C[Past-only portfolio rules]
    C --> D[Costs + accounting]
    D --> E[Returns and drawdowns]
    D --> F[VaR and tail diagnostics]
    D --> G[Regime stress and uncertainty]
    E --> H[Reproducible research output]
    F --> H
    G --> H
    H --> I[Report and dashboard]
~~~

## Run ATLAS

**Python 3.11–3.13 recommended.** Download the code, then:

~~~bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[all]'
python -m pytest -q
streamlit run app.py
~~~

On Windows, activate the environment using **.venv\Scripts\activate**.

The dashboard starts with a clearly labeled **synthetic engineering fixture**; this is for demonstration and **is not** the historical finding above.

### Reproduce the archived historical analysis

~~~bash
python -m atlas.real_study --output results/real_market --repetitions 500
~~~

This downloads the three exact archives pinned by Git commit and verifies the file bytes before allowing historical-source claims. Raw vendor OHLCV is **not committed or redistributed**.

You can also run it on GitHub: **Actions → Pinned historical ETF audit → Run workflow**. The successful [reference run](https://github.com/yavuzaksoyy06-create/ATLAS-Cross-Asset-Trading-Risk-Research/actions/runs/39064709600) generated an English empirical research memo, interactive HTML dashboard, performance and stress tables, VaR coverage diagnostics, cost-sensitivity tables, bootstrap results and reproduction checksums. **Artifacts are subject to GitHub retention periods.**

Local offline mode is documented in [REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md) and can validate byte-identical archived downloads. Uploaded personal CSVs and synthetic price fixtures are *never* mislabeled as audited vendor data.

## Research integrity: what the evidence does not say

1. **No alpha claims.** Better realized downside outcomes in one interval do not imply predictive value, economic deployability or outperforming SPY.
2. **No untouched holdout.** The post-2023 period had been inspected before the study was published.
3. **Source adjustments not independently audited.** The public archive states that ETF closes account for corporate actions, but no licensed-vendor reconciliation was performed. Data rights also remain unverified.
4. **Trading costs are assumptions.** Fixed bps do not replicate actual depth, spread, impact, funding, borrowing, taxes or real fills.
5. **Model validation is not approval.** VaR exception tests have finite-sample limitations; no internal bank model, market-making inventory or institutional trading infrastructure is claimed.
6. **Market proxies are not all markets.** The three ETFs include overlapping equity exposures and were selected retrospectively.

## Technical documentation

- [Empirical evidence and interpretation](research/real_market_2018_2025/EMPIRICAL_FINDINGS.md)
- [Research methodology and formulas](docs/RESEARCH_METHODOLOGY.md)
- [Source provenance and reproducibility](docs/REPRODUCIBILITY.md)
- [Market risk and failure-mode register](docs/MODEL_RISK_REGISTER.md)
- [Simulated trading-desk workflow](docs/TRADING_DESK_WORKFLOW.md)
- [Recruiter-ready project brief and resume wording](docs/RECRUITER_BRIEF.md)
- [Release notes](RELEASE_NOTES.md)

**Bottom line:** ATLAS is an end-to-end, transparent research demonstration for **evaluating trading decisions and risk models**, with repeatable computation and documented limitations. Independent project; not investment advice.
