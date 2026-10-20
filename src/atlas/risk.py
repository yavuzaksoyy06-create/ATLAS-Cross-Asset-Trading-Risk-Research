"""Historical risk, performance and hypothetical scenarios."""
from __future__ import annotations
import numpy as np
import pandas as pd

# Hypothetical single-step price shocks; not historical replay or forecasts.
STRESS_SCENARIOS = {
    "Equity selloff (hypothetical)": {"SPY": -.10, "QQQ": -.14, "IWM": -.15,
        "EEM": -.14, "TLT": .04, "IEF": .015, "GLD": .025, "UUP": .025, "HYG": -.07, "BIL": 0.0},
    "Rates spike (hypothetical)": {"SPY": -.04, "QQQ": -.07, "IWM": -.06,
        "EEM": -.05, "TLT": -.12, "IEF": -.05, "GLD": -.05, "UUP": .02, "HYG": -.04, "BIL": 0.0},
    "Credit stress (hypothetical)": {"SPY": -.08, "QQQ": -.09, "IWM": -.12,
        "EEM": -.11, "TLT": .025, "IEF": .01, "GLD": .035, "UUP": .03, "HYG": -.10, "BIL": 0.0},
}


def historical_var_es(daily: pd.Series, confidence: float = .95) -> tuple[float, float]:
    """1-day historical loss VaR and expected shortfall in decimal return units.

    Positive values mean positive possible LOSSES, not guaranteed realized losses.
    Negative thresholds are floored at 0, which is useful for loss-only reporting.
    """
    x = pd.Series(daily).dropna().to_numpy(dtype=float)
    if len(x) < 30 or not 0 < confidence < 1 or not np.isfinite(x).all():
        raise ValueError("Need 30+ finite returns and confidence in (0,1).")
    losses = -x
    threshold = float(np.quantile(losses, confidence))
    es = float(losses[losses >= threshold].mean())
    return max(threshold, 0.0), max(es, 0.0)


def performance_stats(daily: pd.Series, annualization: int = 252) -> dict[str, float]:
    x = pd.Series(daily, dtype=float).dropna()
    if len(x) < 30 or not np.isfinite(x.to_numpy()).all() or (x <= -1).any():
        raise ValueError("Need 30+ finite returns above -100%.")
    annual_return = float((1 + x).prod() ** (annualization / len(x)) - 1)
    vol = float(x.std(ddof=1) * np.sqrt(annualization))
    sharpe = float(x.mean() / x.std(ddof=1) * np.sqrt(annualization)) if x.std(ddof=1) > 0 else float("nan")
    equity = (1 + x).cumprod()
    # Original invested capital is also a peak; an initial loss must count.
    drawdown = equity / equity.cummax().clip(lower=1.0) - 1
    var, es = historical_var_es(x)
    return {"total_return": float(equity.iloc[-1] - 1),
            "annualized_return": annual_return, "annualized_vol": vol,
            "sharpe_zero_rf": sharpe, "max_drawdown": float(drawdown.min()),
            "historical_var_95_1d": var, "historical_es_95_1d": es,
            "positive_days_fraction": float((x > 0).mean())}


def stress_portfolio(weights: pd.Series, nav_usd: float = 1_000_000) -> pd.DataFrame:
    if nav_usd <= 0 or abs(weights.sum() - 1) > 1e-6:
        raise ValueError("Positive NAV and normalized weights required.")
    rows = []
    for name, shocks in STRESS_SCENARIOS.items():
        missing = [k for k in weights.index if k not in shocks and weights[k] > 1e-10]
        if missing:
            raise ValueError(f"Scenario has no shock for holdings: {missing}")
        pnl_fraction = float(sum(weights.get(t, 0.0) * shocks.get(t, 0.0) for t in weights.index))
        rows.append({"scenario": name, "portfolio_return": pnl_fraction,
                     "estimated_pnl_usd": pnl_fraction * nav_usd})
    return pd.DataFrame(rows).set_index("scenario")


def risk_contributions(returns: pd.DataFrame, weights: pd.Series,
                       lookback: int = 252) -> pd.DataFrame:
    """Euler contribution to portfolio volatility using sample covariance."""
    history = returns[weights.index].tail(lookback)
    if len(history) < 30:
        raise ValueError("Need 30+ observations.")
    cov = history.cov().to_numpy() * 252
    w = weights.to_numpy(dtype=float)
    var = float(w @ cov @ w)
    vol = float(np.sqrt(max(var, 0)))
    marginal = cov @ w / vol if vol > 0 else np.zeros_like(w)
    return pd.DataFrame({"weight": w, "vol_contribution": w * marginal,
                         "vol_contribution_share": w * marginal / vol if vol > 0 else 0.0},
                        index=weights.index)


def var_coverage_backtest(daily: pd.Series, lookback: int = 252,
                          confidence: float = .95) -> tuple[pd.DataFrame, dict]:
    """Ex ante rolling 1-day historical VaR; unconditional Kupiec exceedance test.

    Dates t use ONLY t-lookback...t-1 returns to compute risk limit for t.
    Returns are observed portfolio returns, not an executable hedge rule.
    """
    from scipy.stats import chi2
    x = pd.Series(daily).dropna()
    if len(x) < lookback + 30:
        raise ValueError("Insufficient observations for rolling VaR coverage.")
    rows = []
    for i in range(lookback, len(x)):
        var, _ = historical_var_es(x.iloc[i - lookback:i], confidence=confidence)
        observed = float(x.iloc[i])
        rows.append((x.index[i], var, -observed, int(-observed > var)))
    frame = pd.DataFrame(rows, columns=["Date", "var_loss_limit", "actual_loss", "exceeded"]).set_index("Date")
    k, n = int(frame.exceeded.sum()), len(frame)
    p0 = 1.0 - confidence
    p_hat = k / n
    # Clip away log(0) in likelihood, while reporting un-clipped observed rate.
    p_safe = np.clip(p_hat, 1e-12, 1 - 1e-12)
    lr = -2 * ((n-k)*np.log(1-p0) + k*np.log(p0) -
               ((n-k)*np.log(1-p_safe) + k*np.log(p_safe)))
    stats = {"observations": n, "exceedances": k, "expected_exceedances": n*p0,
             "observed_rate": p_hat, "target_rate": p0,
             "kupiec_lr": float(max(lr, 0)), "kupiec_p_value": float(chi2.sf(max(lr, 0), df=1))}
    return frame, stats
