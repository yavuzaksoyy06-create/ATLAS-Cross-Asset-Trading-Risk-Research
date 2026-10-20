# ATLAS 2.0 — Master roadmap

Only **Stage 0** is authorized and implemented in this work. The sequence below is a **proposed development contract**, derived from the user's platform vision, not a recovered or approved set of later-stage prompts. Future user prompts may revise it. Each stage requires its own review and the universal definition of done in `ENGINEERING_STANDARDS.md`.

## Objective and boundaries

Build a professional educational/research platform for discretionary traders, prop candidates, systematic traders and quantitative researchers. Preserve the original cross-asset empirical research. The differentiator is a Trade Intelligence Engine that connects decisions to contemporaneous evidence, compares feasible alternatives and separates observed facts from modeled hypotheses. More charts or higher backtest returns do not establish that capability.

Start as a modular extension of the existing Python package and Streamlit application. Add durable storage/API boundaries only as requirements justify them. No forced frontend rewrite, paid data, public deployment or live order routing is authorized.

## Stage deliverables and acceptance

| Stage | Scope and actual deliverables required | Specific exit evidence, in addition to universal standards |
|---|---|---|
| **0 — Audit and preservation** | Inventory, executed tests, narrow corrections, five documents, safe branch and original-file hashes | Existing historical reference reconciles; old research unchanged; defects/blocked routes disclosed; owner receives report. Stop. |
| **1 — Platform foundations and data contracts** | Explicit instrument/bar/source/run schemas; as-of/timezone/adjustment contracts; validated configuration; portable dependency setup; package resource strategy; version metadata; source/legacy adapters | Source and wheel smoke tests include historical reference resources; source checkout remains reproducible; reject duplicate/NaN/late data; immutable fixture IDs; no legacy numerical drift; signed-off license scope or synthetic-only mode. |
| **2 — Market workspace** | Rights-compatible market adapters, OHLC charts where available, watchlists and scanners with real computed filters; source/freshness labels | Hand-checked scan results, persistent watchlist CRUD, empty/stale/error states, timestamp alignment and representative measured UI response times; no invented feed freshness or price action. |
| **3 — Journal and portfolio ledger** | Timestamped journal, instrument/position/cash/fee events, imports and auditable edits, reconciliation and export | Double-entry or equivalently reconcilable balance identities; exact small trade cases; fees/partial fills/corrections; idempotent imports and event ordering; user-data isolation. Research weights remain distinct from book holdings. |
| **4 — Backtesting and execution simulation** | Versioned strategies, walk-forward runner, reusable simple benchmarks, spread/slippage/partial-fill/latency assumptions, reproducible runs | Future-mutation tests, corporate-action/calendar cases, independently calculated trade/fee P&L, no same-bar execution advantage, constraints and small-case optimizer validation; report costs and sensitivity. |
| **5 — Portfolio risk intelligence** | Portfolio concentration, drawdown, VaR/ES, historical and hypothetical stress, supported factor/exposure views and explainable risk limits | Risk unit/time-horizon consistency, breach backtests with rare-event caveats, dependence/forecast-timing tests, invalid/stale risk data fails closed; instrument coverage honestly bounded. |
| **6 — Paper trading and replay** | Durable paper order lifecycle, paper fills, replay clock, state recovery, journal/ledger/risk integration | Deterministic replay; restart/retry/duplicate-event tests; cash/position reconciliation; cancellation/partial fills; explicit paper identity; no reachable live submission path. |
| **7 — Trade Intelligence Engine** | Decision snapshots, entry/exit/sizing analysis, feasible counterfactual simulator, evidence cards, behavioral/strategy weakness diagnostics | Counterfactuals obey contemporaneous data/capital/liquidity constraints; distinguish observed outcome, assumed alternative and causal claim; blind/time-held-out case evaluation; uncertainty and failure cases; reproduce explanations from evidence IDs. |
| **8 — Microstructure and market-making research** | Independently labeled simulation or lawfully sourced quotes/order books; inventory/spread/queue research | Inventory and cash conservation, latency/adverse-selection assumptions, queue/fill limitations, baseline policies and sensitivity; no executable RFQ or market-making profitability claims from invented ADV. |
| **9 — AI-assisted research** | Optional grounded assistant over permitted project evidence; tool access restricted to read/research actions; deterministic fallback | Citation/data verification, numeric consistency, unknown-answer behavior, prompt-injection/untrusted-document tests, cost controls; no unapproved model spend and no trade authorization capability. |
| **10 — Integration, hardening and portfolio release** | Cohesive tested workspace, quality dashboard, documented setup, CI/security/performance gates, demo and case studies | Browser end-to-end tests, failure recovery, reproducible benchmarks and resource measurements, rights review, accurate screenshots, reviewed release and no fabricated deployment/users/ROI. Hosting is a separate approval. |

Stages 4–6 may inform one another but are not to be developed simultaneously without an approved scope change. The ledger and timestamp contracts precede counterfactual decision analysis. Price licensing and source quality are prerequisites for a market-facing product, not blockers to synthetic foundation tests.

## Exact Stage 1 readiness criteria

Stage 1 may **start only after owner review** when all of the following hold:

- [x] Baseline commit and preserved-file manifest are recorded; work is isolated from `main`.
- [x] Five Stage 0 documents exist, with required module inventory and actual execution evidence.
- [x] Original 43 tests pass; the corrected full local suite passes 69 tests, including 24 regressions and two UI interactions.
- [x] Full pinned historical run reconciles 48 metrics; eight before/after historical files are byte-identical; archived research and assets remain preserved.
- [x] Known broken wheel route, absent code license, unverified data rights/adjustments and incomplete test boundaries are explicit, with acceptance criteria below/in the audit.
- [ ] Review the remote Stage 0 commit/PR and its exact-head CI status (recorded at delivery; failures must be investigated).
- [ ] Owner accepts the Stage 0 report, chooses/approves the Stage 1 scope and explicitly authorizes continuing.

Stage 1 is **not** ready to claim a deployable trading product. Required Stage 1 exit fixes include wheel reference resources (`D-01`), environment/version contract (`D-02`), dataset/engine identity (`D-03`) and authoritative timestamps/source labels. An approved code license and documented data-use permission are necessary before broader redistribution; otherwise preserve restricted historical research and use synthetic fixtures for new modules.

## Parking lot

Live trading, broker credentials, institutional regulatory validation, paid data, a production multi-user service, causal profitability claims and prospective alpha certification are outside this roadmap's authorization. They require explicit separate decisions, evidence and approvals.
