# CV and technical-interview guide

## Defensible project title

**ATLAS | Cross-Asset Trading and Market Risk Research Platform — Python**

## Resume wording (after independently rerunning the pinned market study)

- Built a modular Python research platform linking transaction-cost-aware asset allocation, drawdown/VaR/expected-shortfall diagnostics, historical stress replays and simulated portfolio trade risk limits.
- Analyzed 2,011 aligned archived ETF price observations (SPY, QQQ, TLT; 2018–2025) and compared three explicit portfolio rules with passive equity exposure, including a cost-matched buy-and-hold benchmark.
- Implemented past-only signal timing, rolling VaR exception backtests (Kupiec/Christoffersen), paired block-bootstrap uncertainty, source-integrity checks and automated software tests.

If the pinned downloader has **not** been run on your machine, say only that a reproducible downloader and independent historical reference calculation are provided. Do not claim that the full enhanced real-data output has been personally reproduced.

## Interview answers to prepare

**Why the project?** A trading analyst evaluates risk-adjusted decisions, not just point forecasts. This project models risk, costs, market regimes and model-validation assumptions in one accountable workflow.

**What did you learn from historical results?** In the retrospective 2023–2025 sample, diversified allocations lowered measured drawdown but gave up returns versus SPY. That result is *not* a claim of alpha; uncertainty, market regimes, financing and implementation matter.

**How did you avoid look-ahead bias?** Weight targets for a held return are functions only of earlier close-to-close observations. Unit tests mutate future observations and assert earlier results remain unchanged. A past-only algorithm does not solve data-selection or survivor bias.

**What's the biggest limitation?** The publicly archived adjusted-price claim was not independently reconciled against a licensed data provider; there is no real bid/ask and the evaluation segment was examined post hoc. Production-grade risk requires verified data, a genuinely untouched window and approved trade execution assumptions.

**Why use Kupiec and Christoffersen?** One tests whether the count of losses beyond the 99% VaR threshold is consistent with a 1% nominal exceedance rate; the other tests independence/clustering and combined conditional coverage. Rare events weaken their statistical power.

**Could a bank use ATLAS tomorrow?** No. It is educational research demonstrating components of a risk-review workflow, not vendor-verified, production-secure, capital-regulatory validated or integrated with bank order management.
