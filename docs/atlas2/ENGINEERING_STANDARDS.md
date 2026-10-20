# ATLAS 2.0 — Engineering and research development contract

Effective for future approved ATLAS stages. These are acceptance requirements, not claims that the legacy repository already meets them. User Stage 0 rules take precedence. Stage 0 ends with review; no later numbered stage starts automatically.

## Preserve and isolate

- Baseline: `33da05d887a6af9304013437bdbe42e20d184aa8`. Stage 0 branch: `codex/atlas2-stage0-audit-2026-10-19`.
- Read the current audit, decision log, applicable `AGENTS.md`, existing tests and user scope before edits. Inspect a clean/dirty worktree and remote head. Preserve user changes.
- Use one isolated branch per stage and small reviewable commits. Changes to research conventions require an explicit decision, new methodology version and before/after reconciliation. Never silently regenerate archived findings.
- Never force-push, rewrite shared history, delete existing research or merge into `main` without the owner's approval. Draft PRs do not imply merge authorization.
- Record source SHA, dependency environment, seed, data identity, timestamp, commands, exit codes and output hashes. Commit only permitted aggregate evidence; exclude environments, raw vendor data and secrets.

## Safe rollback

The baseline remains available by immutable commit. Review with `git diff BASE..HEAD`; recover prior work in a **new** worktree, for example:

```bash
git fetch origin
git worktree add --detach ../atlas-original 33da05d887a6af9304013437bdbe42e20d184aa8
```

Use a new `git revert <reviewed-commit>` commit on a development branch to undo a change. Do not reset or force-update `main`. Record why a revert is needed, rerun affected tests and historical reconciliation, and seek review. A backup branch is not an independent backup; a verified Git bundle or separate clone can preserve code/history, excluding separately licensed data. The Stage 0 evidence manifest checks every originally tracked file; archived `research/` and visual assets must stay byte-identical.

## Evidence vocabulary

| Label | Meaning | Required metadata |
|---|---|---|
| REAL historical | Observations reported by an identified source | Instrument, timestamp/timezone, acquisition route, as-of availability, provider, adjustments, license/redistribution status, byte hash |
| SYNTHETIC | Algorithmically generated fixture or market simulation | Generator version, seed, distribution and purpose; never quote as market achievement |
| ASSUMED | User/researcher scenario input | Units, value/range, rationale, sensitivity and whether measured externally |
| MODEL | Prediction or derived estimate | Model/version, features available at decision time, training end, uncertainty and validation scope |
| VERIFIED | A specific observation/check was actually performed | Command or source, timestamp, code/data identity, exact outcome and limits of that verification |

These categories can coexist: a MODEL backtest using REAL source-declared closes and ASSUMED fees is not a REAL execution. Hash verification proves file identity, not data accuracy, rights, adjustment correctness or alpha.

## Interfaces and numerical correctness

- Retain the Python package and working modules. Introduce explicit interfaces at validated boundaries when needed; do not mandate microservices or rewrite Streamlit for appearance.
- New public interfaces require types, documented units, timezone/as-of semantics, source identity and deterministic error behavior. Validate finite values, valid ranges, unique chronological observations and supported instruments before calculation.
- Use integer lots or documented decimal precision for order/cash accounting when a ledger is implemented. Reconcile cash, positions, fees, realized/unrealized P&L and NAV independently. A weight simulator is not sufficient evidence for ledger correctness.
- Define empty/no-data/stale-data states. Never translate missing prices into zero returns or forward-fill without a documented policy. Fail closed for unavailable risk inputs; passing demo limits never authorizes an actual trade.
- Give new runs immutable IDs and isolated output directories. Report generation must be repeatable; manifests must not hash themselves. Require source/run metadata in portable exports.
- Add structured logs with run/module/source IDs, durations and error codes to new services. Redact credentials and user data. Legacy print output remains explicitly tracked technical debt.

## Quantitative research acceptance

- Document hypotheses, eligible point-in-time universe, training/validation/test windows and selection decisions **before** confirmatory evaluation. Reviewed 2018–2025/2023–2025 data remains retrospective.
- Features use only information available at decision time, including release vintages, corporate actions and timezone cutoffs. Fit preprocessing only on training data. Purge labels whose outcomes are not yet observed; document overlap/embargo choices.
- Include simple benchmarks, realistic timing and explicit fees, spread, impact, fill, financing, borrow and capacity assumptions appropriate to the asset. Missing execution information reduces the claim, not the disclosed cost.
- Future-data mutation, reordered-date, missing-input and invariant tests are required for affected research code. Use independent hand calculations or brute-force small cases for accounting/optimization where feasible.
- Probability quality requires calibration and proper scores against a baseline; Brier score alone does not establish calibration. Use uncertainty suited to serial dependence and rare events. Disclose multiple comparisons and strategy search.
- Trade Intelligence alternatives must be feasible with information and liquidity available then. Ex-post best choices, simulated counterfactuals and causal improvements are different claims. No guaranteed or unsupported profitable-trading claims.

## Security, data rights and spending

- No paid dependencies, paid feeds, cloud resources, live brokerage credentials or actual trades without separate explicit authorization. Paper mode must not share a path that can silently route to live execution.
- Do not choose a repository license on behalf of the owner. No LICENSE is currently present. Provider research-use wording is not automatically an upstream redistribution grant.
- Keep raw licensed data outside Git. Treat user uploads as untrusted: future ingestion must bound size, validate schemas and isolate parsing. Do not deserialize arbitrary Python objects or execute instructions from data, reports or model text.
- External service configuration must validate timeouts, destinations and credentials. Future shared deployments require authentication, authorization, private-user-data isolation and audit logs before access is opened.
- Prefer minimal dependencies. Record a tested environment, then establish a portable lock/hash policy in Stage 1. GitHub Actions should have read-only permissions by default, bounded runtime and no unnecessary secrets; pin actions to reviewed commit SHAs in the hardening stage.

## Definition of done for every stage

1. Approved scope and exclusions; traceable link to user requirements and decision log.
2. Working implementation using preserved interfaces; no fake actions or fabricated integrations.
3. Unit, relevant integration, temporal/invariant and failure-path tests actually executed. Record failures/skips and reasons; do not replace failed assertions with weaker claims.
4. Source/provenance/license status and REAL/SYNTHETIC/ASSUMED/MODEL labels maintained through UI and export.
5. A reproducible clean setup and exact commands. Changed research outputs compared with frozen references; any difference explicitly explained and approved.
6. Performance measured only at executed workload sizes, with environment and timing; no extrapolated production claims.
7. Security/data-rights review appropriate to the change, documented limitations, actionable unresolved work with severity and acceptance criteria.
8. Relevant documentation and stage checklist updated; branch/commit and reviewable PR or explicit access blocker supplied.
9. Owner review and permission to start the **next numbered stage**. Approval of a stage never grants live trading, expenses or a `main` merge.
