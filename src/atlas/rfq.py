"""Illustrative client RFQ, never a live bid/ask or executable quote."""
from __future__ import annotations
from dataclasses import dataclass
import math
import pandas as pd
from .risk import historical_var_es, stress_portfolio


@dataclass
class RFQResult:
    side: str
    ticker: str
    notional_usd: float
    mid_reference: float
    simulated_quote: float
    total_markup_bps: float
    updated_weights: pd.Series
    before_var95_usd: float
    after_var95_usd: float
    before_stress: pd.DataFrame
    after_stress: pd.DataFrame


def simulate_rfq(weights: pd.Series, returns: pd.DataFrame, latest_mid: float,
                 ticker: str, side: str = "sell", notional_usd: float = 20_000,
                 nav_usd: float = 1_000_000, assumed_adv_usd: float = 50_000_000,
                 spread_bps: float = 4.0) -> RFQResult:
    """Hypothetical funded trade against BIL reserve, long-only.

    `side` refers ONLY to the simulated portfolio's buy/sell action. No
    customer order book, dealer/client side, or market-maker inventory is modeled.
    """
    if side not in {"buy", "sell"} or ticker == "BIL" or ticker not in weights:
        raise ValueError("Choose 'buy'/'sell' on a supported non-BIL asset.")
    if "BIL" not in weights or nav_usd <= 0 or notional_usd <= 0 or assumed_adv_usd <= 0 or latest_mid <= 0:
        raise ValueError("Positive monetary inputs and BIL funding proxy required.")
    if not 0 < notional_usd / nav_usd <= 1:
        raise ValueError("Trade notional must not exceed current portfolio NAV.")
    if not abs(weights.sum() - 1) < 1e-6 or (weights < -1e-9).any():
        raise ValueError("Long-only normalized weights required.")
    move = (1 if side == "buy" else -1) * notional_usd / nav_usd
    after = weights.copy()
    after[ticker] += move
    after["BIL"] -= move
    if (after < -1e-9).any():
        raise ValueError("Insufficient asset to sell or cash-like BIL reserve to buy.")
    after = after.clip(lower=0) / after.clip(lower=0).sum()
    sigma = float(returns[ticker].tail(21).std())
    # SPREAD, volatility surcharge and sqrt(participation) impact: invented
    # educational coefficients/ADV assumption; NOT a real execution model.
    markup = spread_bps/2 + 0.10 * sigma * 10_000 + 20 * math.sqrt(notional_usd/assumed_adv_usd)
    quote = latest_mid * (1 + markup/10_000 if side == "buy" else 1 - markup/10_000)
    before_returns = returns[weights.index] @ weights
    after_returns = returns[after.index] @ after
    before_var, _ = historical_var_es(before_returns)
    after_var, _ = historical_var_es(after_returns)
    return RFQResult(side=side, ticker=ticker, notional_usd=notional_usd,
                     mid_reference=latest_mid, simulated_quote=quote,
                     total_markup_bps=markup, updated_weights=after,
                     before_var95_usd=before_var*nav_usd, after_var95_usd=after_var*nav_usd,
                     before_stress=stress_portfolio(weights, nav_usd),
                     after_stress=stress_portfolio(after, nav_usd))
