# ATLAS | Recruiter & Technical Interview Brief

## One-line portfolio description

**ATLAS — Cross-Asset Trading & Risk Intelligence:** A Python research platform for cost-aware portfolio backtesting, historical stress analysis, VaR model validation and risk-gated desk simulations, backed by a reproducible historical ETF audit.

## Why the project is relevant to Global Markets

ATLAS demonstrates the workflow a junior trading or markets analyst needs to understand: **assess market exposures, test a trading or allocation hypothesis, price in implementation costs, quantify downside, challenge risk estimates, and communicate both results and limitations**. It is an independent educational project—not bank experience, actual market making, investment advice or a claim of profitable execution.

## CV | Best concise version (two bullets)

**ATLAS — Cross-Asset Trading & Risk Intelligence | Python, Quantitative Research**

- Developed a modular Python research platform integrating transaction-cost-aware portfolio backtesting, historical stress replays, VaR/expected-shortfall diagnostics, and simulated trade risk-limit checks.
- Analyzed **2,010 daily historical ETF return observations** (SPY, QQQ, TLT; 2018–2025); implemented rolling 99% VaR backtesting, reproducibility checks and GitHub Actions-based numerical reconciliation across **48 reference metrics**.

Suggested portfolio link:
https://github.com/yavuzaksoyy06-create/ATLAS-Cross-Asset-Trading-Risk-Research

## CV | Markets / trading alternative (one bullet)

- Built ATLAS, a Python cross-asset risk research platform analyzing ETF allocation, transaction costs, historical crisis scenarios and 99% VaR breaches; reproduced 2018–2025 market-proxy research with automated tests and a 48-metric audit.

## LinkedIn | Project description

**ATLAS — Cross-Asset Trading & Risk Intelligence**

Designed a reproducible Python research workflow connecting portfolio construction, market-risk measurement, historical stress testing and simulated trading-desk decisions.

The historical case study evaluates SPY, QQQ and TLT over 2,010 daily return observations (2018–2025). It compares transparent allocation rules with passive equity exposure after modeled transaction costs, investigates the contrasting effects of 2020 and 2022 stress regimes, and backtests rolling 99% VaR forecasts using Kupiec and Christoffersen diagnostics.

Built with a focus on **reproducibility, transparent model assumptions and interpretation of unsuccessful strategies**, rather than unsupported claims of predictive alpha.

**Skills:** Python · Pandas · NumPy · SciPy · scikit-learn · Quantitative Research · VaR · Expected Shortfall · Portfolio Risk · Backtesting · Model Validation · GitHub Actions

## 30-second interview explanation

> “ATLAS is a quantitative markets and risk research platform I developed in Python. I wanted to move beyond simple portfolio optimization by including implementation costs, stress regimes and independent risk-model checks. Using archived SPY, QQQ and TLT prices from 2018 to 2025, I tested three allocation approaches against a passive benchmark. A key result was that diversification reduced drawdowns in some periods but failed during the 2022 duration shock. I also found that some 99% VaR models produced substantially more exceptions than expected. The project is reproducible, but I am careful not to claim alpha or production readiness.”

## 90-second follow-up structure

**Research problem:** Trade proposals should be evaluated beyond forecast returns, including risk and implementation.

**Method:** Three long-only ETF allocation rules; 21-session rebalancing; fixed 8-bp turnover-cost assumption; benchmark with initial transaction cost; risk metrics, stress periods and past-only rolling VaR.

**What the empirical output actually showed:** 2023–2025 60/40 had a -12.70% drawdown versus -18.76% for SPY, but 13.33% versus 23.00% CAGR. During the 2022 inflation/duration episode, the 60/40 strategy lost more than SPY (-27.13% versus -23.83%). For costed SPY, the 99% Gaussian EWMA model had 42 observed exceptions in 1,758 forecasts versus 17.58 expected.

**Engineering:** Clear data provenance, deterministic reference comparison, code tests, CI and on-demand pinned historical audit; GitHub Actions generated research reports.

**Limitations:** The data archive's corporate-action adjustments are not independently validated, the test segment was previously reviewed, and daily closes/fixed transaction costs are approximations rather than real fills.

## Questions reviewers may ask

**Does lower drawdown mean your portfolio beat the benchmark?**
No. Risk reduction and excess return are different questions. In this sample the diversified allocations delivered lower CAGR. The exploratory bootstrap comparisons did not establish alpha.

**Why did the 60/40 strategy fail in 2022?**
Rates and inflation repricing hit both equities and long-duration Treasury ETFs. Correlations and bond hedging behaviour are regime-dependent.

**What does a 99% VaR breach tell you?**
A loss exceeded the one-day threshold predicted to be breached around 1% of the time. Exceedance frequency and clustering should be tested. More breaches than expected can indicate model misspecification or regime changes; finite-sample tests are not guarantees.

**How did you avoid look-ahead leakage?**
Allocation and risk forecasts use only information available before the held return; testing includes controls against future-data dependence. This does not resolve ETF universe selection or retrospective hypothesis selection.

**Could a financial institution deploy this now?**
No. This is a transparent educational research prototype; deployment would need licensed and reconciled data, point-in-time histories, executable quote/order book information, financing and liquidity modeling, governance, monitoring and operational controls.

**What is the source of the historical prices?**
A public GitHub archive pinned to a specific commit. The code verifies bytes and 48 reference-calculated metrics reconcile. The archive's adjusted-price claims have not been cross-checked against a licensed independent provider.

## Do not say in applications

- “I built a JPMorgan/Golman Sachs institutional trading platform.”
- “My ML model predicts markets accurately.”
- “The strategy beats the market.”
- “The data is vendor-certified / independently adjusted.”
- “I ran a pristine out-of-sample test.”
- “This is a production-ready trading execution system.”

**Direct evidence:** [Empirical findings](../research/real_market_2018_2025/EMPIRICAL_FINDINGS.md) · [Research methodology](RESEARCH_METHODOLOGY.md) · [Successful market audit](https://github.com/yavuzaksoyy06-create/ATLAS-Cross-Asset-Trading-Risk-Research/actions/runs/39064709600)
