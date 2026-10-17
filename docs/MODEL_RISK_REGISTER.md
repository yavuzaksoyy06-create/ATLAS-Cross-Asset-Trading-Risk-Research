# ATLAS | Model risk register

| Risk | Severity | Why it matters | Current treatment | Next control |
|---|---|---|---|---|
| Third-party adjusted prices may contain unverified dividend/split methods | High | Spurious ETF total return and tail estimates | Source commit + blob hashes, explicit unverified status | Reconcile against licensed provider |
| Survivorship / universe hindsight | High | Ex-post ETF selection may flatter any strategy | Only three declared ETFs; no universe generalization | Point-in-time eligible investment set |
| Reviewed test period | High | Post-hoc results cannot validate discovered alpha | Label 2023–25 as retrospective | Reserve future preregistered untouched samples |
| Execution modeling | High | Close-price fills ignore spreads, impact, time and liquidity | Modeled 8 bps, 0–30 bps sensitivity | Quotes, bid/ask/volume and slippage by state |
| Benchmark asymmetry | Medium | Zero-cost SPY boosts passive comparison unfairly | Add costed SPY buy-and-hold with initial purchase cost | Include cash, coupons, distributions and liquidation fees |
| VaR tail assumptions | High | Risk exceptions cluster; 99% violations are rare | Rolling HS/EWMA, Kupiec/Christoffersen | Intraday loss, volatility regime tests, rare-event intervals |
| Cross-asset proxy interpretation | Medium | TLT has duration/credit/microstructure distinct from direct bonds | Explicit ETF-only label | Duration DV01, term-structure, FX/credit hedges |
| Model selection and multiple comparisons | High | Optimizing after test inspection inflates false discoveries | Fixed 3-rule comparison, disclose lack of correction | Preregister evaluation and correction for family of tests |
| ML classifier | Medium | Probability calibration may fail under shifted classes | Purged expanding walk-forward, base-rate Brier benchmark | Calibration curves and genuinely held-out data |
| Simulated RFQ economics | High | Invented ADV, quote and risk limits aren't executable | All RFQ figures marked hypothetical, fail-closed gate | Real quote, inventory, approved limits, independent pricing |
| Vendor licensing/redistribution | High | Unauthorized republication of raw financial data | No third-party OHLCV bundled | Legal/data-provider verification |
| Dependency and source drift | Medium | Upgraded software changes results; pinned archive may disappear | Exact source Git commit, hashes, output checksums | Pinned reproducible lock file and lawful immutable snapshot |

Risks are not remedied by unit tests alone. The architecture deliberately treats *model validity*, *software correctness* and *economic deployability* as three separate questions.
