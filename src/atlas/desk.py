"""Educational portfolio trade approval gate and auditable decision memorandum.

Direction denotes the PORTFOLIO action only (not a client/market maker side).
All spreads/ADV are labelled assumptions, not observed quotes or liquidity.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import math
import pandas as pd
from .rfq import simulate_rfq, RFQResult


@dataclass(frozen=True)
class RiskLimits:
    max_position_fraction: float = 0.40
    max_var95_usd: float = 30_000
    max_stress_loss_usd: float = 120_000
    max_daily_adv_participation: float = 0.02
    max_incremental_var95_usd: float = 8_000

    def __post_init__(self) -> None:
        if (not 0 < self.max_position_fraction <= 1
                or self.max_var95_usd <= 0 or self.max_stress_loss_usd <= 0
                or not 0 < self.max_daily_adv_participation <= 1
                or self.max_incremental_var95_usd < 0):
            raise ValueError("Risk limits must be positive, finite sensible limits.")
        if not all(math.isfinite(x) for x in asdict(self).values()):
            raise ValueError("Risk limits must be finite.")


@dataclass
class TradeDecision:
    decision: str
    reasons: list[str]
    risk_before_var95_usd: float
    risk_after_var95_usd: float
    incremental_var95_usd: float
    worst_stress_loss_after_usd: float
    adv_participation: float
    portfolio_side: str
    asset: str
    notional_usd: float
    estimated_markup_bps: float
    hypothetical_quote: float
    pricing_caveat: str


def decide_trade(weights: pd.Series, returns: pd.DataFrame, mid: float, ticker: str,
                 side: str, notional_usd: float, nav_usd: float,
                 assumed_adv_usd: float, limits: RiskLimits = RiskLimits(),
                 spread_bps: float = 4.0) -> tuple[TradeDecision, RFQResult]:
    """Propose a funded trade, then fail closed on individually named risk breaches."""
    if len(returns) < 30 or not returns.index.is_monotonic_increasing:
        raise ValueError("30+ sorted returns required for risk assessment.")
    if not math.isfinite(assumed_adv_usd) or assumed_adv_usd <= 0:
        raise ValueError("Finite positive assumed ADV required.")
    if not math.isfinite(notional_usd) or notional_usd <= 0:
        raise ValueError("Positive finite notional required.")
    quote = simulate_rfq(weights, returns.tail(252), latest_mid=mid,
                         ticker=ticker, side=side, notional_usd=notional_usd,
                         nav_usd=nav_usd, assumed_adv_usd=assumed_adv_usd,
                         spread_bps=spread_bps)
    participation = notional_usd / assumed_adv_usd
    increment = quote.after_var95_usd - quote.before_var95_usd
    worst_stress = max(0.0, float(-quote.after_stress.estimated_pnl_usd.min()))
    reasons = []
    if float(quote.updated_weights.max()) > limits.max_position_fraction + 1e-10:
        reasons.append(f"POSITION_LIMIT: largest weight {quote.updated_weights.max():.2%} > {limits.max_position_fraction:.2%}")
    if quote.after_var95_usd > limits.max_var95_usd:
        reasons.append(f"VAR_LIMIT: 95% historical 1d VaR ${quote.after_var95_usd:,.0f} > ${limits.max_var95_usd:,.0f}")
    if increment > limits.max_incremental_var95_usd:
        reasons.append(f"INCREMENTAL_VAR_LIMIT: delta ${increment:,.0f} > ${limits.max_incremental_var95_usd:,.0f}")
    if worst_stress > limits.max_stress_loss_usd:
        reasons.append(f"SCENARIO_LIMIT: worst hypothetical shock loss ${worst_stress:,.0f} > ${limits.max_stress_loss_usd:,.0f}")
    if participation > limits.max_daily_adv_participation:
        reasons.append(f"ADV_PARTICIPATION_LIMIT: {participation:.2%} > {limits.max_daily_adv_participation:.2%}")
    if not reasons:
        reasons.append("All configured synthetic-book risk limits passed; not a production approval.")
    d = TradeDecision(
        decision="REJECT" if any("LIMIT:" in x for x in reasons) else "PASS_DEMO_LIMITS",
        reasons=reasons, risk_before_var95_usd=quote.before_var95_usd,
        risk_after_var95_usd=quote.after_var95_usd, incremental_var95_usd=increment,
        worst_stress_loss_after_usd=worst_stress, adv_participation=participation,
        portfolio_side=side, asset=ticker, notional_usd=notional_usd,
        estimated_markup_bps=quote.total_markup_bps, hypothetical_quote=quote.simulated_quote,
        pricing_caveat="Invented spread/impact coefficients and ADV; not executable, client-related, or calibrated."
    )
    return d, quote


def write_decision_memo(decision: TradeDecision, limits: RiskLimits, destination: str | Path,
                        data_source: str, observation_end: str) -> None:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"decision": asdict(decision), "limits": asdict(limits),
              "data_origin": data_source, "last_observation": observation_end,
              "calibration": "ASSUMPTIONS ONLY, not live or institutional data"}
    path.with_suffix(".json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    rows = "\n".join(f"- {reason}" for reason in decision.reasons)
    md = f"""# ATLAS | Hypothetical Trade Decision

**Decision:** {decision.decision}  
**Market data:** {data_source}  
**Last observed session:** {observation_end}  
**Portfolio action:** {decision.portfolio_side.upper()} {decision.asset} — ${decision.notional_usd:,.0f}

## Before/after portfolio risk (historical estimates)

- 1d 95% VaR before: ${decision.risk_before_var95_usd:,.2f}
- 1d 95% VaR after: ${decision.risk_after_var95_usd:,.2f}
- Incremental VaR: ${decision.incremental_var95_usd:,.2f}
- Largest hypothetical scenario loss after: ${decision.worst_stress_loss_after_usd:,.2f}
- Assumed ADV participation: {decision.adv_participation:.2%}

## Limit checks

{rows}

## Pricing assumptions

- Illustrative quote: ${decision.hypothetical_quote:,.4f} (not executable)
- Estimated all-in markup: {decision.estimated_markup_bps:.2f} bps
- {decision.pricing_caveat}

**Methodology:** Historical 252-session weighted portfolio return VaR and
synthetic scenario shocks; cash is approximated by BIL (not literal cash).
Limits are illustrative and do not constitute regulated risk approval or advice.
"""
    path.with_suffix(".md").write_text(md, encoding="utf-8")
