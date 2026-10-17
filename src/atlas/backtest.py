"""Daily close-to-close simulator with strict past-only signals and cost accounting.

At the end of t-1, compute target weights using returns through t-1.
Apply this target to next close-to-close interval ending t. Costs accrue on
rebalance as approximation; NO claims of executable close-price fills.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd
from .strategies import STRATEGIES


@dataclass
class BacktestResult:
    daily_returns: pd.Series
    equity: pd.Series
    weights: pd.DataFrame
    turnover: pd.Series
    costs: pd.Series
    strategy: str


def run_backtest(returns: pd.DataFrame, strategy: str = "regime",
                 rebalance_every: int = 21, fee_bps: float = 3.0,
                 slippage_bps: float = 5.0, min_training_days: int = 126) -> BacktestResult:
    if strategy not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {strategy}")
    if returns.empty or len(returns) < 2 or returns.isna().any().any():
        raise ValueError("Clean, nonempty historical return panel required.")
    if not np.isfinite(returns.to_numpy()).all() or (returns <= -1).any().any():
        raise ValueError("Returns must be finite and above -100%.")
    if rebalance_every < 1 or min_training_days < 1 or min_training_days >= len(returns):
        raise ValueError("Rebalance and warmup parameters are invalid.")
    if fee_bps < 0 or slippage_bps < 0:
        raise ValueError("Costs cannot be negative.")
    universe = list(returns.columns)
    current = pd.Series(0.0, index=universe)
    daily, turnover, costs, weights = [], [], [], []
    strategy_fn = STRATEGIES[strategy]
    for i, (_, row) in enumerate(returns.iterrows()):
        # Warmup portfolio is in the cash proxy, if available. Never peek into row.
        if i == 0:
            current = pd.Series(0.0, index=universe)
        if i % rebalance_every == 0:
            history = returns.iloc[:i]  # STRICT: excludes return at day i and all later
            if i < min_training_days:
                target = pd.Series(0.0, index=universe)
                target["BIL" if "BIL" in universe else universe[0]] = 1.0
            else:
                target = strategy_fn(history).reindex(universe).fillna(0)
            if (target < -1e-12).any() or not np.isclose(target.sum(), 1.0, atol=1e-8):
                raise ValueError("Invalid long-only target weights.")
            trades = float((target - current).abs().sum())
            current = target.copy()
        else:
            trades = 0.0
        exposure = current.copy()
        cost_fraction = trades * (fee_bps + slippage_bps) / 10_000.0
        gross = float(np.dot(exposure.to_numpy(), row.to_numpy()))
        net = (1 - cost_fraction) * (1 + gross) - 1
        if net <= -1:
            raise ValueError("Portfolio exhausted; review input data/cost assumptions.")
        daily.append(net)
        turnover.append(trades)
        costs.append(cost_fraction)
        weights.append(exposure.to_numpy())
        # Drift target by market returns, ready for next day's turnover calculation.
        current = exposure.mul(1 + row) / (1 + gross)
    d = pd.Series(daily, index=returns.index, name=strategy)
    return BacktestResult(
        daily_returns=d,
        equity=(1 + d).cumprod().rename("equity"),
        weights=pd.DataFrame(weights, index=returns.index, columns=universe),
        turnover=pd.Series(turnover, index=returns.index, name="turnover"),
        costs=pd.Series(costs, index=returns.index, name="cost_fraction"),
        strategy=strategy,
    )
