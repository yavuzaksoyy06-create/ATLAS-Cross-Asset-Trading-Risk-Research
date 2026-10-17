# An illustrative desk workflow

The proposed workflow is designed for a junior quantitative / market risk analyst supporting a generic markets team. It is not based on a financial institution's confidential operating process.

**08:30 — Market monitor.** Check updated daily prices, data gaps, asset return distributions and major realized risk events. Keep a timestamped source manifest rather than trusting a dashboard's visual freshness.

**09:00 — Research an allocation idea.** Compare fixed baseline allocations to an interpretable trailing-volatility rule. Show capital funding assumptions, net turnover and adverse market regimes; avoid announcing alpha based solely on a sharp equity curve.

**10:30 — Portfolio review.** Summarize gross/net performance, factor concentration, one-day historical VaR and expected shortfall. Identify sensitivities such as SPY/QQQ joint exposure and TLT duration exposure.

**11:00 — Client inquiry illustration.** Given an assumed client trade size and reference adjusted close, estimate an *illustrative* quote adjustment and before/after portfolio sensitivity. The risk gate checks funded holdings, concentration, 95% VaR, stressed loss and hypothetical ADV constraints. A `PASS_DEMO_LIMITS` is **never** a live trading permission.

**12:00 — Validate model risk.** Compare past-only 99% VaR forecasts with subsequent observed loss exceedances. Report exception counts, LR tests, and explain sparse-event reliability rather than cherry-pick the model with the smallest number of violations.

**13:00 — Write a decision memo.** Export the risk decision, assumptions, scenario impact, data lineage, measurement dates and veto rationale. Disclose missing real quote data and bid/ask microstructure. Separate proposed trades from market trades actually executed.

**Next development stage:** Add time-stamped internal paper-trading ledger, cash financing, real execution simulator with spreads and regulatory controls, and approved external data; until then ATLAS remains a research prototype.
