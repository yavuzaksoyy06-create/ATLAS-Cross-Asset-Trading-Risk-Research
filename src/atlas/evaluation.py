"""Predeclared chronological evaluation and paired block-bootstrap uncertainty.

Multiple candidate strategy comparisons are exploratory and do not certify
alpha. No tuning decisions may be based on the test segment.
"""
from __future__ import annotations
from dataclasses import dataclass
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .backtest import run_backtest
from .risk import performance_stats
from .strategies import STRATEGIES


@dataclass
class EvaluationResult:
    summary: pd.DataFrame
    daily_holdout: pd.DataFrame
    methodology: dict


def paired_block_bootstrap(excess: pd.Series, block_size: int = 21,
                           repetitions: int = 500, seed: int = 2026) -> tuple[float, float]:
    """95% CI for annualized mean excess return (not annual CAGR excess).

    Stationary dependence approximated by resampling circular contiguous blocks.
    This heuristic does not address multiple testing or nonstationary regimes.
    """
    x = np.asarray(excess.dropna(), dtype=float)
    n = len(x)
    if n < 60 or not np.isfinite(x).all() or not 1 <= block_size <= n or repetitions < 100:
        raise ValueError("Need 60+ finite paired samples and 100+ resamples.")
    rng = np.random.default_rng(seed)
    nblocks = int(np.ceil(n / block_size))
    starts = rng.integers(n, size=(repetitions, nblocks))
    offsets = np.arange(block_size)
    samples = x[((starts[..., None] + offsets) % n).reshape(repetitions, -1)[:, :n]]
    values = samples.mean(axis=1) * 252
    return tuple(np.quantile(values, [.025, .975]).astype(float))


def evaluate_fixed_strategies(returns: pd.DataFrame, test_start: str | pd.Timestamp,
                              strategies: tuple[str, ...] = ("equal", "inverse_vol", "momentum", "regime", "cvar"),
                              fee_bps: float = 3, slippage_bps: float = 5,
                              rebalance_every: int = 21, block_size: int = 21,
                              repetitions: int = 500, seed: int = 2026) -> EvaluationResult:
    """Evaluate all pre-declared rules on a fixed date split, full prior warmup.

    The date and strategy set MUST be fixed before reviewing test results;
    this function cannot technically enforce the user's research process.
    """
    if (returns.empty or not isinstance(returns.index, pd.DatetimeIndex)
            or not returns.index.is_monotonic_increasing or returns.index.has_duplicates):
        raise ValueError("Date-sorted, unique DatetimeIndex panel required.")
    if len(set(returns.columns)) != len(returns.columns):
        raise ValueError("Duplicate assets not allowed.")
    if returns.isna().any().any() or not np.isfinite(returns.to_numpy()).all():
        raise ValueError("Missing or invalid returns.")
    chosen = tuple(strategies)
    if not chosen or any(s not in STRATEGIES for s in chosen) or len(set(chosen)) != len(chosen):
        raise ValueError("Strategies must be unique known rules.")
    t0 = pd.Timestamp(test_start)
    if t0.tzinfo is not None:
        t0 = t0.tz_localize(None)
    is_test = returns.index >= t0
    train_count, test_count = int((~is_test).sum()), int(is_test.sum())
    if train_count < 252 or test_count < 90:
        raise ValueError("Need at least 252 pre-test and 90 held-out sessions.")
    if "SPY" in returns:
        bench = returns.loc[is_test, "SPY"]
        benchmark_label = "SPY adjusted-price proxy (no execution costs)"
    else:
        bench = returns.loc[is_test].iloc[:, 0]
        benchmark_label = f"{returns.columns[0]} adjusted-price proxy (no execution costs)"
    result_columns: dict[str, pd.Series] = {"benchmark": bench}
    records = []
    for j, strategy in enumerate(chosen):
        bt = run_backtest(returns, strategy=strategy, rebalance_every=rebalance_every,
                          fee_bps=fee_bps, slippage_bps=slippage_bps)
        holdout = bt.daily_returns.loc[is_test]
        result_columns[strategy] = holdout
        excess = holdout - bench
        lower, upper = paired_block_bootstrap(excess, block_size, repetitions, seed + j)
        perf = performance_stats(holdout)
        records.append({
            "strategy": strategy, "holdout_start": str(holdout.index[0].date()),
            "holdout_end": str(holdout.index[-1].date()),
            "sessions": len(holdout), "total_return_net": perf["total_return"],
            "annualized_return_net": perf["annualized_return"],
            "sharpe_zero_rf": perf["sharpe_zero_rf"],
            "max_drawdown": perf["max_drawdown"],
            "annualized_mean_excess_vs_benchmark": float(excess.mean() * 252),
            "bootstrap_95ci_excess_mean_low": lower,
            "bootstrap_95ci_excess_mean_high": upper,
            "trading_turnover_holdout": float(bt.turnover.loc[is_test].sum()),
            "estimated_cost_fraction_sum": float(bt.costs.loc[is_test].sum()),
        })
    meta = {
        "study": "PREDECLARED RULE COMPARISON; not a fitted or certified alpha experiment",
        "test_start_requested": str(t0.date()), "test_start_observed": str(returns.index[is_test][0].date()),
        "training_sessions": train_count, "test_sessions": test_count,
        "strategy_set": list(chosen), "benchmark": benchmark_label,
        "fee_bps": fee_bps, "slippage_bps": slippage_bps,
        "rebalance_sessions": rebalance_every, "bootstrap_block_sessions": block_size,
        "bootstrap_repetitions": repetitions, "bootstrap_seed": seed,
        "limits": [
            "Holdout is only untouched if date/parameters were fixed before looking at its outcomes.",
            "Each strategy may use training-period history and previous test-session observations; never the current return.",
            "Block-bootstrap confidence intervals are heuristic with serial dependence and finite sample risk.",
            "Multiple strategies create data-snooping risk; CI is not corrected for multiple hypotheses.",
            "Benchmark is an uncosted passive index/ETF proxy; differences are not a causal or executable alpha estimate.",
            "Test reports on synthetic data are engineering checks, not market results.",
        ],
    }
    return EvaluationResult(pd.DataFrame.from_records(records).set_index("strategy"),
                            pd.DataFrame(result_columns), meta)


def write_evaluation(result: EvaluationResult, output: str | Path) -> None:
    path = Path(output)
    path.mkdir(parents=True, exist_ok=True)
    result.summary.to_csv(path / "fixed_holdout_comparison.csv")
    result.daily_holdout.to_csv(path / "fixed_holdout_daily.csv", index_label="Date")
    (path / "evaluation_methodology.json").write_text(
        json.dumps(result.methodology, indent=2), encoding="utf-8")
