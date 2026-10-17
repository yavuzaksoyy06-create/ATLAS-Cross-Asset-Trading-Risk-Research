# ATLAS quantitative-research publication checklist

## Completed engineering checks

- [x] Unit and integration tests, CI across Python 3.11–3.13 (workflow configured; hosted CI status not observed yet).
- [x] Offline end-to-end synthetic research execution, explicitly labeled not market data.
- [x] Source-class verification in generated research reports and standalone CSV exports.
- [x] Fixed rebalance timing, lagged signal construction and future-timestamp mutation test.
- [x] Fee/slippage modeling and a one-time costed passive-equity comparator.
- [x] 95%/99% VaR/ES diagnostics, historical-simulation and Gaussian-EWMA exception tests.
- [x] Circular paired-block bootstrap with exploratory multiplicity warning.
- [x] Independent archival reference comparison code and source identities pinned in the repository.
- [x] Professional English README, methodology, model risk and CV/interview note.

## Necessary before claiming market-result replication is complete

- [ ] On a networked computer, run `python -m atlas.real_study --output results/real_market` (no `--input-csv`) to download and verify all three pinned archived CSV files.
- [ ] Confirm `results/real_market/reference_reconciliation.json` says `PASSED_REFERENCE_NUMERICAL_RECONCILIATION`. If it fails, investigate numerical differences; do not disable the check to force a pass.
- [ ] Examine the full empirical report and historic crisis chart generated **from the genuine pinned archive**, not the synthetic demo.
- [ ] Independently reconcile adjusted closes and total-return treatment with a properly licensed second provider; unresolved at publication.
- [ ] Obtain a genuinely untouched future evaluation set before any alpha claim, with strategy and execution assumptions pre-registered.
- [ ] Push new repository and review hosted GitHub Actions result; connected GitHub currently provides file operations but no confirmed new-repository creation.

## Interview integrity

- The project is an educational desk-oriented simulator, not deployed sell-side trading infrastructure.
- Trading quotes and market impact are simulated, not actual broker fills.
- The archived data analysis is independent retrospective research; 2023–2025 was inspected in advance and is not a pristine holdout.
- Do not say source provider adjustments or commercial redistribution rights were independently certified.
- The synthetic offline smoke test **never** demonstrates profitable strategy behavior in actual markets.
