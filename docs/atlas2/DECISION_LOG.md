# ATLAS 2.0 — Decision log

Dates below are UTC; the resumed audit continued on 20 October. Only Stage 0 is authorized. This log records decisions and rejected alternatives without modifying historical research records.

| ID / date | Decision | Evidence and consequences |
|---|---|---|
| A2-000 / 2026-10-19 | Shelve PromiseIQ; use the existing ATLAS repository as authority | Explicit user instruction. Prior-conversation search returned an error; partial ATLAS file context was found, but no missing stage prompts were invented. |
| A2-001 / 2026-10-19 | Isolate Stage 0 at baseline `33da05d887a6af9304013437bdbe42e20d184aa8` on `codex/atlas2-stage0-audit-2026-10-19` | Local and remote development branch created. No main merge, history rewrite or forced update. Baseline hashes cover 59 tracked files. |
| A2-002 / 2026-10-19 | Run the original installation and tests before corrections | Fresh editable installation succeeded; initial premature test attempt failed while dependencies were installing and is retained. Original 43 tests subsequently passed. |
| A2-003 / 2026-10-19 | Perform actual full pinned historical download and reconciliation | 2,011 closes / 2,010 returns; 48 metrics matched before and after fixes. Earlier successful GitHub historical run also observed. No independent vendor adjustment or rights validation is implied. |
| A2-004 / 2026-10-19 | Correct demonstrated defects F-01–F-08, preserve numerical method conventions | Input validation, initial-capital drawdown, binary exceptions, finite comparison tolerance and non-self-referential manifest. Regression failures saved before fixes. Eight historical outputs remain byte-identical. No strategy tuning. |
| A2-005 / 2026-10-19 | Preserve both backtest/risk-summary paths | Cost timing, warm-up and quantile conventions differ. Unifying them now would invalidate continuity without an approved methodology migration. Record D-03 for explicit contracts. |
| A2-006 / 2026-10-19 | Use Streamlit AppTest for actual server-side interactions; do not claim browser validation | Synthetic screen, VaR button and empty CSV state passed. An initial widget-selector test mistake was fixed. A separate dashboard CI job is added; no UI redesign. |
| A2-007 / 2026-10-19 | Treat wheel historical failure as an open distribution blocker | Wheel built/installed, then failed at missing repository-relative reference JSON. Editable/source setup works. Resource packaging belongs in Stage 1; do not advertise standalone wheel reproducibility meanwhile. |
| A2-008 / 2026-10-19 | Keep REAL, SYNTHETIC, ASSUMED, MODEL and VERIFIED scopes distinct | Synthetic ML Brier underperformed base rate. RFQ economics remain assumptions. No claim of calibrated ML, prospective alpha, live fills, institution affiliation or profit improvement. |
| A2-009 / 2026-10-19 | Retain original empirical outputs and old release integrity record | Four manifest hashes were already stale at baseline. New audit evidence documents current facts; historical records are not rewritten to appear newly verified. |
| A2-010 / 2026-10-19 | Defer licenses, external rights and deployment approvals | Code has no LICENSE; upstream research wording does not settle data rights. No license chosen for owner, no paid service, public deployment or live order path enabled. |
| A2-011 / 2026-10-19 | Propose a roadmap without treating it as prior approved scope | Stage 1–10 definitions are a proposal derived from the user's vision. User review is required before Stage 1; future prompts may replace sequencing. |
| A2-012 / 2026-10-19 | Preserve failed audit attempts and measure only actual execution | Premature install test, coverage source misconfiguration and test-harness errors are disclosed. Corrected local checkpoint: 68 passes, followed by the 69-test compatibility check below. Coverage includes package pytest execution only, not separate CLI runs or browser rendering. |
| A2-013 / 2026-10-19 | Deliver a development checkpoint for review, never merge | Commit/branch and any PR/hosted CI status are provided at handoff. Rollback uses a new revert/worktree, not history rewriting. No next stage is started. |

| A2-014 / 2026-10-20 | Preserve single-asset ML compatibility while validating timestamps | New failing regression demonstrated the overly strict Stage 0 validator reuse. An explicit `minimum_assets=1` ML validation option preserves prior functionality; portfolio defaults remain two assets. Final suite: 69 passes. |
| A2-015 / 2026-10-20 | Publish via connected GitHub app when direct Git authentication is unavailable | CLI push returned a username/authentication error; use an atomic tree based on the original tree and a non-forced ref update with expected-head lease. Retain local checkpoint history; verify the published tree equals the tested local tree. |

## Pending owner decisions

1. Review Stage 0 and authorize the exact Stage 1 scope.
2. Approve a code license and permitted data-use/redistribution policy before expanded distribution.
3. Approve future methodology versions before any engine unification or changed historical results.
4. Separately authorize any future expense, hosting or live financial execution; none is implied by this audit.
