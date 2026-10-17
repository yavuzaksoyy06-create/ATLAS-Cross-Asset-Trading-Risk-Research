"""Simple, interpretable, lagged decision rules. No future data is consumed."""
from __future__ import annotations
import numpy as np
import pandas as pd


def _weight(universe: list[str], allocations: dict[str, float]) -> pd.Series:
    w = pd.Series(0.0, index=universe)
    for ticker, val in allocations.items():
        if ticker in w.index:
            w[ticker] = val
    if w.sum() <= 0:
        raise ValueError("Strategy has no supported assets.")
    return w / w.sum()


def equal_weight(history: pd.DataFrame) -> pd.Series:
    """Always-invested baseline, including cash-like BIL only if supplied."""
    return pd.Series(1 / history.shape[1], index=history.columns, dtype=float)


def inverse_volatility(history: pd.DataFrame, lookback: int = 63,
                       universe: list[str] | None = None) -> pd.Series:
    columns = list(history.columns)
    eligible = [x for x in (universe or columns) if x in columns]
    if not eligible:
        raise ValueError("No supported instruments.")
    if len(history) < lookback:
        return _weight(columns, {x: 1.0 for x in eligible})
    vol = history[eligible].iloc[-lookback:].std().clip(lower=1e-5)
    inverse = 1.0 / vol
    weights = inverse / inverse.sum()
    return _weight(columns, weights.to_dict())


def momentum_rotation(history: pd.DataFrame, lookback: int = 126,
                      top_n: int = 3) -> pd.Series:
    """Six-month total-return momentum; positive-score assets only; else BIL."""
    cols = list(history.columns)
    cash = "BIL" if "BIL" in cols else cols[-1]
    if len(history) < lookback:
        return _weight(cols, {cash: 1.0})
    eligible = [x for x in cols if x != cash]
    scores = (1 + history[eligible].iloc[-lookback:]).prod() - 1
    chosen = scores[scores > 0].nlargest(top_n).index.tolist()
    return _weight(cols, {x: 1.0 for x in chosen} if chosen else {cash: 1.0})


def market_regime(history: pd.DataFrame) -> dict:
    """Transparent heuristic, not a calibrated probability or trained ML model."""
    if "SPY" not in history or len(history) < 126:
        return {"label": "Insufficient history", "volatility": None,
                "momentum": None, "vol_percentile": None}
    spy = history["SPY"]
    mom = float((1 + spy.iloc[-126:]).prod() - 1)
    rolling = spy.rolling(21).std() * np.sqrt(252)
    vol = float(rolling.iloc[-1])
    prev = rolling.dropna().iloc[-252:]
    percentile = float((prev <= vol).mean())
    is_risk_off = bool(mom < 0 or percentile > .80)
    return {"label": "Risk-Off" if is_risk_off else "Risk-On",
            "volatility": vol, "momentum": mom, "vol_percentile": percentile}


def regime_allocation(history: pd.DataFrame) -> pd.Series:
    cols = list(history.columns)
    state = market_regime(history)["label"]
    if state == "Insufficient history":
        return _weight(cols, {"BIL": 1.0} if "BIL" in cols else {cols[0]: 1.0})
    if state == "Risk-Off":
        return _weight(cols, {"BIL": .50, "IEF": .30, "GLD": .20})
    return inverse_volatility(history, universe=["SPY", "QQQ", "IWM", "EEM", "HYG"])

def cvar_allocation(history: pd.DataFrame) -> pd.Series:
    """Constrained empirical tail-risk optimizer. See optimization module."""
    from .optimization import min_cvar_weights
    return min_cvar_weights(history)


STRATEGIES = {"equal": equal_weight, "inverse_vol": inverse_volatility,
              "momentum": momentum_rotation, "regime": regime_allocation,
              "cvar": cvar_allocation}
