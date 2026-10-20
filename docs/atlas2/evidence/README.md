# Stage 0 execution evidence

These are actual local executions. An exit code of 0 refers only to the recorded command, not general platform correctness. Failed setup/test-harness attempts are deliberately retained. See `../STAGE_0_AUDIT.md` for causes and the final disposition.

All paths in logs identify the original Linux audit workspace. For reproduction, replace that checkout prefix with your own; run the commands from the repository root in the recorded Python environment. Timings are single-run subprocess wall times, sometimes concurrent, with network/cache effects. They are not controlled scalability benchmarks.

| Run | UTC start | Exit | Wall seconds | Exact command / output |
|---|---|---:|---:|---|
| baseline-tests | 2026-10-19T15:42:31.511846+00:00 | 2 | 1.178 | [baseline-tests.json](baseline-tests.json) / [log](baseline-tests.log) |
| baseline-historical | 2026-10-19T15:43:03.466230+00:00 | 0 | 34.843 | [baseline-historical.json](baseline-historical.json) / [log](baseline-historical.log) |
| baseline-installed-tests | 2026-10-19T15:43:03.520745+00:00 | 0 | 12.929 | [baseline-installed-tests.json](baseline-installed-tests.json) / [log](baseline-installed-tests.log) |
| regression-before | 2026-10-19T15:43:54.067207+00:00 | 1 | 28.02 | [regression-before.json](regression-before.json) / [log](regression-before.log) |
| audit-tool-install | 2026-10-19T15:44:14.976449+00:00 | 0 | 18.527 | [audit-tool-install.json](audit-tool-install.json) / [log](audit-tool-install.log) |
| wheel-build | 2026-10-19T15:44:15.633188+00:00 | 0 | 15.542 | [wheel-build.json](wheel-build.json) / [log](wheel-build.log) |
| regression-after | 2026-10-19T15:45:03.513653+00:00 | 1 | 9.97 | [regression-after.json](regression-after.json) / [log](regression-after.log) |
| compile | 2026-10-19T15:45:27.328735+00:00 | 0 | 0.684 | [compile.json](compile.json) / [log](compile.log) |
| dashboard-tests | 2026-10-19T15:45:27.333141+00:00 | 1 | 16.288 | [dashboard-tests.json](dashboard-tests.json) / [log](dashboard-tests.log) |
| wheel-install | 2026-10-19T15:45:27.442981+00:00 | 0 | 5.05 | [wheel-install.json](wheel-install.json) / [log](wheel-install.log) |
| pip-check | 2026-10-19T15:45:28.081313+00:00 | 0 | 1.039 | [pip-check.json](pip-check.json) / [log](pip-check.log) |
| final-suite | 2026-10-19T21:15:23.641692+00:00 | 2 | 3.025 | [final-suite.json](final-suite.json) / [log](final-suite.log) |
| corrected-historical | 2026-10-19T21:15:39.867502+00:00 | 0 | 13.107 | [corrected-historical.json](corrected-historical.json) / [log](corrected-historical.log) |
| yahoo-smoke | 2026-10-19T21:15:39.867503+00:00 | 0 | 10.575 | [yahoo-smoke.json](yahoo-smoke.json) / [log](yahoo-smoke.log) |
| wheel-historical | 2026-10-19T21:15:39.868253+00:00 | 1 | 22.611 | [wheel-historical.json](wheel-historical.json) / [log](wheel-historical.log) |
| synthetic-fixture | 2026-10-19T21:15:39.868254+00:00 | 0 | 0.525 | [synthetic-fixture.json](synthetic-fixture.json) / [log](synthetic-fixture.log) |
| synthetic-study | 2026-10-19T21:15:40.434681+00:00 | 0 | 1.878 | [synthetic-study.json](synthetic-study.json) / [log](synthetic-study.log) |
| desk-cli | 2026-10-19T21:15:52.712216+00:00 | 0 | 6.322 | [desk-cli.json](desk-cli.json) / [log](desk-cli.log) |
| suite-final | 2026-10-19T21:16:00.554933+00:00 | 0 | 16.191 | [suite-final.json](suite-final.json) / [log](suite-final.log) |
| baseline-window-check | 2026-10-19T21:16:21.928954+00:00 | 1 | 1.407 | [baseline-window-check.json](baseline-window-check.json) / [log](baseline-window-check.log) |
| single-asset-regression-before | 2026-10-20T10:30:30.024372+00:00 | 1 | 2.724 | [single-asset-regression-before.json](single-asset-regression-before.json) / [log](single-asset-regression-before.log) |
| suite-final-followup | 2026-10-20T10:30:41.134348+00:00 | 0 | 26.944 | [suite-final-followup.json](suite-final-followup.json) / [log](suite-final-followup.log) |
| final-historical | 2026-10-20T10:31:39.225896+00:00 | 0 | 30.01 | [final-historical.json](final-historical.json) / [log](final-historical.log) |

The successful final pytest run is **suite-final-followup** (69 tests); **suite-final** preserves the earlier 68-test checkpoint. **baseline-installed-tests** is the original unchanged 43-test suite. **wheel-historical** remains a genuine open failure. The original install was observed successful before baseline tests but its full pip log was not retained; no install wall time is invented.

Additional artifacts:

- `environment.json` and `environment-freeze.txt`: actual package versions, not a hash lock.
- `coverage.txt`: package-only pytest coverage; separate CLI/historical runs are outside its measurement.
- `baseline-files-sha256.json`, `original-file-preservation.json`: original file identities and preservation result.
- `historical-preservation.json`: eight original/corrected research outputs compared byte for byte.
- `historical-reference_reconciliation.json`, `historical-reproduction_manifest.json`, `historical-performance_summary.csv`, `historical-risk_model_diagnostics.csv`: source metadata and permitted aggregate outputs, not raw vendor prices.
- `hosted-baseline-ci.json`: observed GitHub main matrix and earlier manual historical run, not Stage 0 head CI.
- `static-inventory.json`: module inventory and limited pattern scan scope.

Original `research/` outputs and the legacy release manifest were not rewritten. No prices, downloaded raw archives, binary wheels or environments are distributed here.
