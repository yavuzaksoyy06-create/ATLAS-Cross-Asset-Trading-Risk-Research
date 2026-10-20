# ATLAS 2.0 — Stage 0 audit

**Disposition: Stage 0 completed for review; conditional readiness for foundation work, not production or trading.** No Stage 1 implementation is included. PromiseIQ is outside this work.

Audited 2026-10-19–20 UTC. Repository: [ATLAS-Cross-Asset-Trading-Risk-Research](https://github.com/yavuzaksoyy06-create/ATLAS-Cross-Asset-Trading-Risk-Research). Original commit: `33da05d887a6af9304013437bdbe42e20d184aa8`. Development branch: `codex/atlas2-stage0-audit-2026-10-19`. `main` is not modified or merged by this stage. The delivery commit/PR is identified in the handoff and Git history; this document deliberately avoids a self-referential commit hash.

## Executive assessment

ATLAS has a useful, reproducible **research core**, not an existing full professional trading platform. Source-based installation, portfolio simulations, risk diagnostics, empirical reporting, a synthetic desk CLI and basic Streamlit interactions were executed successfully. The full pinned historical study was downloaded and rerun both before and after corrections. All **48 reference metrics** reconciled, with maximum reported absolute difference **0.0 percentage points at eight-decimal comparison precision**, against a 0.05 pp threshold. Eight numerical output files were byte-identical before/after the changes.

The original 43 tests passed after installation. Additional adversarial checks exposed input-validation, drawdown, exception-count and output-manifest defects. Narrow fixes now pass a **69-test local suite**. This does not establish production safety: the installed-wheel historical route is demonstrably broken, probability calibration is unproven, and data rights/adjustments remain unresolved.

The repository was inspected end to end: 59 originally tracked files; 21 package modules; package/dependency configuration; seven original test files; two workflows; Streamlit UI; report templates, research reference data, aggregate tables, SVG/PNG assets and existing documentation. See [EXISTING_CAPABILITIES.md](EXISTING_CAPABILITIES.md) and [static inventory](evidence/static-inventory.json). Prior-conversation search failed; retrieved ATLAS file context was secondary. Current repository contents and the user's Stage 0 instructions governed this audit.

## Environment and executed evidence

Local environment: Linux 6.18.55 x86_64 / glibc 2.39; CPython **3.12.14**; 9 visible CPUs. Fresh `.venv`, editable package **1.2.0**; NumPy 2.5.4, pandas 3.0.6, SciPy 1.18.1, Plotly 7.1.0, scikit-learn 1.9.1, pytest 9.1.1, Streamlit 1.66.0, yfinance 1.7.0. Coverage 7.16.2 was added as an audit tool, not a runtime dependency. Full [environment](evidence/environment.json) and [observed freeze](evidence/environment-freeze.txt) are retained. The freeze is evidence, **not a portable hash-locked environment**.

All commands below ran from the repository root unless their arguments specify an isolated target. Each `evidence/<id>.json` records exact arguments, UTC start, subprocess wall duration and exit code; its `.log` contains output. Timings are single runs on this environment, with some commands run concurrently and network/caching variation; they are not capacity benchmarks.

| Evidence ID / actual command | Observed outcome |
|---|---|
| Initial `python -m venv .venv` then `.venv/bin/python -m pip install -e '.[all]'` | Fresh install completed, exit 0. Original full pip log and elapsed time were not retained; installed versions are recorded. |
| `baseline-installed-tests`: `.venv/bin/python -m pytest -ra` | **43 passed**, 11.48 s pytest / 12.929 s wall, before source changes. |
| `baseline-historical`: `.venv/bin/python -m atlas.real_study --output results/stage0_baseline_historical --repetitions 500` | Passed full HTTPS pinned download, 48 comparisons and report generation; 34.843 s wall. |
| `regression-before`: `.venv/bin/python -m pytest tests/test_stage0_regressions.py -ra` | 17 failed, 6 passed before corrections; failures retained. Test-harness correction described below. |
| `suite-final`: `.venv/bin/python -m coverage run --branch --source=src/atlas -m pytest -ra` | **68 passed, no skips**, 15.11 s pytest / 16.191 s wall. Includes original 43, 23 audit regressions and 2 Streamlit AppTests at that checkpoint. |
| `suite-final-followup`: `.venv/bin/python -m coverage run --branch --source=src/atlas -m pytest -ra` | **69 passed, no skips**, 25.79 s pytest / 26.944 s wall on 2026-10-20. Adds a single-asset ML compatibility regression. |
| `compile`: `.venv/bin/python -m compileall -q src app.py` | Exit 0. |
| `pip-check`: `.venv/bin/python -m pip check` | Exit 0; no broken dependency requirements. Not a vulnerability scan. |
| `corrected-historical`: `.venv/bin/python -m atlas.real_study --output results/stage0_corrected_historical --repetitions 500` | Passed full pinned download/reconciliation/report after changes; 13.107 s wall. Not evidence of a speed optimization. |
| `final-historical`: `.venv/bin/python -m atlas.real_study --output results/stage0_final_historical --repetitions 500` | Final source passed full pinned reconciliation and reporting on 2026-10-20; 30.01 s wall. Eight outputs remain byte-identical to baseline. |
| `synthetic-fixture`: `.venv/bin/python examples/generate_synthetic_fixture.py` | Created explicitly synthetic 925-row fixture. |
| `synthetic-study`: `.venv/bin/python -m atlas.real_study --input-csv examples/synthetic_3etf.csv --synthetic-fixture --repetitions 100 --output results/stage0_synthetic` | Full synthetic study passed, 1.878 s wall. No historical-performance claim. |
| `desk-cli`: `.venv/bin/python -m atlas --source synthetic --strategy regime --freeze-data --evaluate --bootstrap-reps 100 --trade-demo --run-ml --output results/stage0_desk` | Snapshot verification, five-rule evaluation, RFQ decision, report/HTML and ML passed; 6.322 s wall. Demo trade rejected for concentration. |
| `yahoo-smoke`: exact Python invocation in log/JSON | Real feed request for SPY/QQQ, 2025-01-02 to exclusive 2025-01-16: **9 × 2** price panel; 10.575 s wall. No prices committed. |
| `wheel-build`: `.venv/bin/python -m pip wheel . --no-deps --wheel-dir results/stage0_wheel` | Built wheel, exit 0. |
| `wheel-install`: `.venv/bin/python -m pip install --no-deps --target results/stage0_wheel_installed results/stage0_wheel/atlas_trading_desk-1.2.0-py3-none-any.whl` | Installed isolated baseline wheel, exit 0. |
| `wheel-historical`: `env PYTHONPATH=.../results/stage0_wheel_installed .venv/bin/python -m atlas.real_study --classic-only --output results/stage0_wheel_historical` | **FAILED, exit 1:** `REFERENCE_RESULTS.json` missing from distribution/repository-relative location after data retrieval. Full exact path in evidence. |

Reproduction commands above use `.venv/bin/python` on Linux; activate the environment and use `python` on other systems. The original failed-wheel command tests the baseline-built artifact; Stage 0 did not change package-resource handling.

### Failures and test-harness mistakes were retained

- `baseline-tests` ran prematurely while pip was still installing: seven collection errors from missing pandas, exit 2. After install finished, the unchanged original suite passed 43 tests. This was an audit orchestration error, not a repository regression.
- `regression-after` initially had 22 passes and one failure because the new missing-return test placed corruption outside the desk's deliberate last-252-session assessment window. The fixture was corrected to place the missing value inside that window. `baseline-window-check` reproduced the corrected failure on a detached **original-code worktree**; the final fixed suite passes it.
- `dashboard-tests` initially had one pass/one failure: the test selected the Instrument widget instead of Data source. Selection now uses the widget's label. The app itself was not changed to satisfy this test.
- `final-suite` initially used an erroneous Coverage source value `app.py`, which prematurely imported the Streamlit entry point and caused NumPy import/collection errors. Restricting measurement to `src/atlas` fixed the harness. The successful command uses `--source=src/atlas`; no UI coverage percentage is claimed.
- Final compatibility review found that reuse of the portfolio validator accidentally rejected a formerly supported single-asset ML input. `single-asset-regression-before` records the failure; ML now opts into one asset while portfolio ingestion keeps its existing two-asset minimum. The final **69-test** suite includes this regression.
- Streamlit reported `use_container_width` deprecation warnings during an earlier UI run; modernization is deferred, not hidden.

### Coverage and checks not executed

Measured only for the final pytest run: **851/1,182 statements (72.00%)**, **225/384 branches (58.59%)**, combined Coverage display **69%**. [Per-file missing lines](evidence/coverage.txt) identify gaps. `cli.py`, `report.py` and `__main__.py` have zero direct pytest coverage despite separate successful CLI execution; downloader/reference success paths are exercised by separate historical commands, not included in that percentage. `research_qa.cost_sensitivity` is largely untested. No coverage target is inferred from lines alone.

Not executed: local Python 3.10/3.11/3.13 interpreters; browser visual/accessibility testing; a valid complete offline `--archive-dir` run; full uploaded-CSV UI stress/security tests; independent licensed-vendor reconciliation; dependency vulnerability audit; comprehensive penetration test; multi-user/load/large-universe benchmarks; live trading. Existing CI at the original main SHA was observed successful for Python 3.11/3.12/3.13; the earlier pinned historical workflow was also observed successful. These are **observed remote results**, distinct from this local run. See [hosted evidence](evidence/hosted-baseline-ci.json). Stage 0 exact-head CI is reported at handoff/PR and must not be inferred from an old badge.

## Justified corrective changes

| ID | Defect demonstrated | Narrow change and preservation |
|---|---|---|
| F-01 | A first-session -50% loss followed by flat returns reported zero max drawdown | Initialize peak at original capital in generic statistics and report chart. Archived historical engine already did this correctly and is unchanged numerically. |
| F-02 | Generic simulator accepted reversed/duplicate dates and NaN costs | Validate chronological unique dates/assets and finite nonnegative costs. Valid calculations preserved. |
| F-03 | Historical simulator converted missing prices into apparently valid zero-return observations | Apply existing price validator before calculation. No new imputation or methodology change. |
| F-04 | NaN/infinite quote inputs or negative spreads could reach demo approval; risk sample could silently drop missing returns | Validate monetary/spread inputs, portfolio/return shape, finite complete assessment-window returns and resulting quote. Fail with `ValueError`, never demo approval. |
| F-05 | Exception diagnostics silently cast fractional values to binary and accepted multidimensional arrays | Check original one-dimensional binary inputs before integer conversion. |
| F-06 | ML feature builder accepted descending timestamps | Reuse price validation before computing features. Added future-mutation probability test, terminal-label semantics test and preservation of the existing single-asset feature contract. |
| F-07 | NaN comparison tolerance could suppress reference discrepancies | Require finite tolerance and finite expected/computed metrics. |
| F-08 | Repeated report publication hashed the previous hash manifest into its replacement | Exclude `OUTPUT_SHA256.json` from its own contents; repeated-publication regression. |

No engine consolidation, new platform module, broker integration or aesthetic refactor was performed. CI now adds a separate Python 3.12 dashboard smoke job plus read-only permissions/timeouts. Build/coverage outputs are ignored. Original research files, reference checks and assets are preserved; baseline checksums are in [baseline-files-sha256.json](evidence/baseline-files-sha256.json).

## Research validity review

- **Timing:** generic and historical allocations use returns strictly before the held observation; rolling VaR uses the preceding window. Mutation tests pass. Execution at an adjusted prior close is still an assumption, not a feasible broker fill guarantee.
- **ML:** scaler/logistic regression fit only on past fully matured labels (`j + horizon <= i` at forecast close). Future mutation leaves earlier features/probabilities unchanged. The target is a terminal five-session return below -3%; overlapping labels are dependent. No reliability curves, recalibration or independent untouched historical evaluation establishes calibrated probabilities.
- **Actual synthetic ML result:** 1,312 forecasts, 117 overlapping event observations; Brier **0.083948** versus base-rate **0.082012**. Lower is better: model underperformed this baseline. These are SYNTHETIC engineering results, not historical alpha.
- **Sample:** surviving ETFs SPY/QQQ/TLT were selected retrospectively; SPY and QQQ overlap. No point-in-time universe/delistings, macro-vintage series or untouched 2023–2025 test set exists. README/model-risk disclosures are confirmed.
- **Costs/accounting:** 8 bps, 3 bp commission + 5 bp slippage, is ASSUMED. No observed spread/depth/impact/borrow/funding/tax/settlement. Generic and historical engines use different approximations. The costed SPY benchmark pays once at 2018 inception; a sliced 2023 segment is continuation, not a new 2023 purchase. Zero-risk-free Sharpe is not excess-of-cash Sharpe.
- **Risk:** 1,758 forecasts imply 17.58 expected 99% breaches. Reproduced SPY counts are **31 historical-simulation / 42 Gaussian EWMA**. These challenge calibration; they do not certify regulatory risk adequacy. Quantile/ES conventions differ between generic and historical summaries; ties and finite samples matter.
- **Inference:** 500 circular paired 21-session bootstrap replications estimate arithmetic mean excess, not CAGR excess. Intervals do not repair nonstationarity, multiple testing, hindsight or reviewed samples. Stress windows are ex-post selected replays.
- **Source quality/rights:** pinned source README explicitly claims adjusted closes and educational/research use with Stooq/Yahoo origins. No independently validated upstream redistribution grant, vendor adjustment audit or point-in-time availability was found. A hash check does not cure this. Raw provider prices were not added to Git.

## Open risks and actionable technical debt

| ID / severity | Evidence / limitation | Required next acceptance; owner |
|---|---|---|
| D-01 High — packaging | Installed wheel cannot find historical reference; root app not bundled | Stage 1 engineering: choose source-only vs distributable package contract, bundle/read reference resource appropriately, run isolated wheel study/CLI tests. |
| D-02 Medium — reproducibility/version | Dependency minimums only; `atlas.__version__` says 0.1.0 vs project 1.2.0; Python >=3.10 declared but CI 3.11–3.13 | Stage 1 engineering: authoritative version/support policy, portable tested constraints/lock, compatible clean install and artifact tests. |
| D-03 High — mixed engine semantics | Different cost formula, warm-up, volatility floor, VaR/ES conventions; generic/UI is not archived method | Stage 1 design: explicit engine/method versions and units; later parity or migration tests before any consolidation. Preserve old empirical outputs. |
| D-04 High — data rights and authenticity | Code has no LICENSE; source wording is not independent provider authorization | Owner/data governance: select code license, record allowed use/storage/redistribution per provider; independent reconciliation before stronger data claims. Synthetic work can continue under review. |
| D-05 High — accounting/execution gap | Weights are not a trade ledger; UI “current” holdings are pre-return exposures; BIL is an ETF proxy | Ledger/execution stages: timestamped holdings, shares/cash reconciliation, spreads/fills/fees and unsupported-instrument behavior; label pre-return exposures in interim UI work. |
| D-06 High — statistical claims | Reviewed samples, universe selection, uncalibrated ML, rare VaR events | Research owner: preregister future tests, point-in-time eligibility, proper baselines/calibration/uncertainty and multiplicity controls; no present alpha claim. |
| D-07 Medium — incomplete boundary tests | Sparse success-path unit tests for reference/CLI, limited optimization edge/optimality tests, missing upload cases | Add tests around actual changed boundaries and documented mathematical invariants; keep separate historical evidence and optional UI CI. |
| D-08 Medium — scale and UX | Synchronous Python loops; VaR O(T×window), dense CVaR scenario matrix, bootstrap memory O(resamples×T); uncapped uploads/cache and no persistence | Measure representative workloads and resource use before choosing caching, sparse matrices, jobs/storage; no current throughput or multi-user claim. |
| D-09 Medium — publication integrity | Legacy manifest has four pre-existing stale file hashes; `GITHUB_UPLOAD.md`/review checklist describe initial upload/offline state; free-form metadata is trusted | Keep original release record; dated audit is current authority. Future run IDs, versioned metadata and bounded exporters; do not reinitialize this repository. |
| D-10 Medium — security/operations | No auth/API boundary/structured logs, dependency audit, lint/type gate; action tags mutable | Add controls as interfaces are introduced, then hardening gates; restrict use to local research until an explicit deployment review. |

The narrow secret-pattern scan found no matches for private-key headers, GitHub-token patterns or AWS access-key patterns across 59 tracked files and 63 unique blobs from 16 baseline commits. This is not a complete secret detector or security certification. Application code contains no actual broker/order-routing implementation.

## Preservation, handoff and next-stage gate

The original release manifest is left intact as a historical record; four hashes already differed at baseline (both workflow files, `.gitignore`, README). Stage 0 records a fresh baseline rather than falsely rewriting that old claim. Eight baseline/corrected historical outputs match byte for byte; [comparison evidence](evidence/historical-preservation.json) and aggregate reconciliation/results are committed. No raw price series, local environments or generated distribution are committed.

Read [ENGINEERING_STANDARDS.md](ENGINEERING_STANDARDS.md) for branch/revert/worktree procedures, [DECISION_LOG.md](DECISION_LOG.md) for choices, and [MASTER_ROADMAP.md](MASTER_ROADMAP.md) for proposed stage definitions. Exact Stage 1 entry criteria: preserved baseline, complete five-file audit, passing corrected suite and historical reconciliation, reviewable remote checkpoint/CI, accepted open limitations, and **explicit owner approval of the next scope**. Those last review decisions remain open. Stop here.
