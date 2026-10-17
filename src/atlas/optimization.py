"""Long-only scenario CVaR optimization via linear programming.

This is a sample-optimized tail-risk allocation, not a predictive alpha model.
Train on past returns only; parameter sensitivity and holdout evaluation needed.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.optimize import linprog


def min_cvar_weights(history: pd.DataFrame, lookback: int = 252,
                     confidence: float = .95, max_position: float = .35,
                     min_expected_daily_return: float | None = None) -> pd.Series:
    """Minimize empirical CVaR with budget, position and mean-return constraints.

    Variables [weights (m), loss_threshold_z (1), scenario_excess_u (n)].
    min z + (1/((1-alpha)*n))*sum(u)
    s.t. -r_i @ weights - z <= u_i; u_i >= 0
         sum(weights) = 1; weights <= max_position
         sample E[returns] >= sample equal-weight E[returns] by default.
    """
    if history.shape[1] < 3 or history.isna().any().any():
        raise ValueError("Need at least 3 assets and no missing observations.")
    m = history.shape[1]
    if max_position < 1 / m or max_position > 1 or not 0 < confidence < 1:
        raise ValueError("Infeasible position limits or confidence level.")
    if len(history) < lookback:
        return pd.Series(1.0 / m, index=history.columns)
    ret = history.iloc[-lookback:].to_numpy(dtype=float)
    n = ret.shape[0]
    mu = ret.mean(axis=0)
    target = float(mu.mean()) if min_expected_daily_return is None else float(min_expected_daily_return)
    c = np.zeros(m + 1 + n)
    c[m] = 1.0
    c[m + 1:] = 1.0 / ((1.0 - confidence) * n)
    # vec = [weights, z, u_0...u_n-1]
    A_ub = np.zeros((n + 1, m + 1 + n))
    A_ub[:n, :m] = -ret
    A_ub[:n, m] = -1.0
    A_ub[np.arange(n), m + 1 + np.arange(n)] = -1.0
    A_ub[n, :m] = -mu
    b_ub = np.zeros(n + 1)
    b_ub[n] = -target
    A_eq = np.zeros((1, m + 1 + n))
    A_eq[0, :m] = 1.0
    solution = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq,
                       b_eq=np.array([1.0]),
                       bounds=[(0.0, max_position)] * m + [(None, None)] + [(0.0, None)] * n,
                       method="highs")
    if not solution.success:
        raise ValueError(f"CVaR optimizer failed: {solution.message}")
    w = pd.Series(np.maximum(solution.x[:m], 0), index=history.columns)
    return w / w.sum()
