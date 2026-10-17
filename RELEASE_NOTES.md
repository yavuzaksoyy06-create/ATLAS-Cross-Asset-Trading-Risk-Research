# ATLAS v1.2 — GitHub Release

**Status:** publication-ready engineering repository; retrospectively derived archived-data reference is separately recorded. The full verified real-market download has not executed in this offline build session.

## New in v1.2

- Added `--archive-dir` for a complete SHA-verified local copy of the pinned ETF archive; rejects modified data rather than calling it a valid pinned source.
- Added manually triggered `Pinned historical ETF audit` GitHub Actions workflow, which verifies the archive, compares historical reference results, computes the institutional report, and uploads aggregate metrics only.
- Added offline tests for the verified-data input route and security guardrails.
- English-only project documentation and GitHub deployment instructions.

## Already present from v1.1

- Daily, funded allocation simulation, turnover/cost accounting and cost-aligned SPY benchmark.
- Risk diagnostics: historical simulation and EWMA 99% VaR, exception counts, Kupiec and Christoffersen statistics.
- Ex-post historical crisis windows, cost sensitivity and paired block-bootstrap intervals.
- Simulation-only dealer RFQ and risk-limited portfolio adjustments.
- Streamlit dashboard, reports, source manifests, SHA output digests, GitHub CI and synthetic offline smoke tests.

## Empirical caveats

- Historical reference results were independently computed from archived SPY, QQQ, TLT prices, **not** via a successful Python download in this offline environment.
- Archived data claims adjusted closes; original vendor adjustments, legal reuse terms and point-in-time availability remain unverified.
- Since 2023–2025 observations have been reviewed, this segment is **not** an untouched out-of-sample holdout.
- None of the simulated or backtested returns establishes a profitable, deployable strategy.
