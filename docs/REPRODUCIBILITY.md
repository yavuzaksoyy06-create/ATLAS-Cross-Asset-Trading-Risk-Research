# Reproducing ATLAS

## 1. Rebuild the Python environment

Use Python 3.10–3.13, create a fresh environment, run `python -m pip install -e '.[all]'` and then `python -m pytest -q`. Use `python -m pip freeze > dependency_versions.txt` if a later audit requires an exact package lock; the repository uses compatible version floors, **not** a cryptographic environment lock.

## 2. Confirm the dataset identity

`python -m atlas.real_study --output results/real_market` downloads SPY, QQQ and TLT from the pinned third-party GitHub commit. Every downloaded file is checked against its expected Git blob SHA1. The script rejects missing sessions, time-range mismatches, duplicate dates and nonpositive prices. The pin is a *reproducibility check*, not proof of legal data use, genuine trade prices or audited dividend corrections. A local source can be supplied with `--input-csv`, but it is not pinned.

For local offline reproduction with exact source CSV files, use `--archive-dir market_data`; per-file Git SHA checks remain enforced even without network access. The study rejects silent mismatches when the three date indexes are not identical. The source dates 2018-01-02 through 2025-12-31 contain 2,011 complete aligned close-price rows. The return panel has 2,010 rows.

## 3. Timing and fee semantics

- Return observation *t* is `P[t] / P[t-1] - 1` based on source-declared adjusted closes.
- Initial portfolio allocation is applied before the first return observation. Portfolio weights are rebalanced every 21 sessions, including initial investment, and drift in between.
- Inverse-volatility weights at *t* use only the up-to-63 trailing returns ending *t-1*. The first investment's warm-up inverse-volatility weights are equal if prior history is insufficient.
- A fixed one-way cost of 8 basis points is applied to sum of absolute trade weight changes; the same fee is modeled for the initial passive SPY purchase in `SPY_buy_hold_net`, but the older zero-cost benchmark is retained and disclosed.
- Costs are model parameters; they are not learned from bid/ask data. Simulation does not reproduce exact market-on-close fills.

## 4. How to interpret the output

`EMPIRICAL_RESEARCH_MEMO.md` includes retrospective performance, crisis-window replay, cost sensitivity, Gaussian EWMA vs historical VaR calibration, and paired block-bootstrap intervals. `reproduction_manifest.json` records all methodology choices. `OUTPUT_SHA256.json` hashes the generated outputs at publication time; regenerating with unchanged code, market files and dependencies should be numerically consistent, though timestamps and floating-point implementations can differ.

Data rights are unresolved for third-party raw files: the repository contains aggregated historical reference results and analysis code, **not** the source price CSV files. Market-data use must comply with the provider's terms.

## 5. What was actually tested by the project author

- Automated Python tests verify synthetic fixtures, cost rules, signal time ordering, historical-window calculations, risk coverage math and local publication pipeline.
- A separate historical reference evaluation was conducted using GitHub-accessed real archived files. See `research/real_market_2018_2025/REFERENCE_RESULTS.json`.
- The independent historical data download from Python was **not run in the offline artifact-build environment**. The GitHub Actions manual workflow provides a reproducible route to complete this acceptance check on a networked runner. Do not state that the full pinned downloader was executed successfully here. Run it on an internet-connected computer before using its enhanced output as an empirical result.
- No contemporaneous execution, broker confirmation, risk committee signoff or independent data-vendor audit was conducted.
