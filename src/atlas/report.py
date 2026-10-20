"""Provenance-forward report generation."""
from __future__ import annotations
from pathlib import Path
import pandas as pd
from .backtest import BacktestResult
from .risk import performance_stats, risk_contributions, stress_portfolio, var_coverage_backtest
from .strategies import market_regime


def write_reports(returns: pd.DataFrame, result: BacktestResult,
                  output_dir: str | Path, provenance: str, nav_usd: float = 1_000_000) -> dict:
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    strategy_metrics = performance_stats(result.daily_returns)
    benchmark = returns["SPY"] if "SPY" in returns else returns.iloc[:, 0]
    base_metrics = performance_stats(benchmark)
    summary = pd.DataFrame({"strategy": strategy_metrics, "benchmark": base_metrics})
    summary.to_csv(out / "performance.csv")
    result.weights.to_csv(out / "daily_weights.csv", index_label="Date")
    result.daily_returns.to_csv(out / "daily_strategy_returns.csv", header=True, index_label="Date")
    (pd.DataFrame({"turnover": result.turnover, "cost_fraction": result.costs})
        .to_csv(out / "trading_costs.csv", index_label="Date"))
    w = result.weights.iloc[-1]
    stress = stress_portfolio(w, nav_usd)
    stress.to_csv(out / "stress_scenarios.csv")
    contributions = risk_contributions(returns, w)
    contributions.to_csv(out / "risk_contributions.csv")
    regime = market_regime(returns)
    coverage, coverage_stats = var_coverage_backtest(result.daily_returns)
    coverage.to_csv(out / "risk_var_coverage.csv")
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        subplot_titles=("Growth of $1 (net of costs)", "Drawdown"),
                        vertical_spacing=.12)
    nav_strategy = result.equity
    nav_benchmark = (1 + benchmark).cumprod()
    fig.add_trace(go.Scatter(x=nav_strategy.index, y=nav_strategy,
                             name=result.strategy, mode="lines"), row=1, col=1)
    fig.add_trace(go.Scatter(x=nav_benchmark.index, y=nav_benchmark,
                             name="SPY benchmark", mode="lines"), row=1, col=1)
    for x, label in ((nav_strategy, result.strategy), (nav_benchmark, "Benchmark")):
        fig.add_trace(go.Scatter(x=x.index, y=x / x.cummax().clip(lower=1.0) - 1,
                                 name=f"{label} drawdown", mode="lines"), row=2, col=1)
    fig.update_layout(title=f"ATLAS | {provenance} | Historical simulation (not live)",
                      height=750, template="plotly_white")
    fig.write_html(str(out / "dashboard.html"), include_plotlyjs=True, full_html=True)
    note = f"""# ATLAS | Research Report

**Data origin:** {provenance}

**Simulation:** Daily close-to-close return approximation. Strategy signals are built strictly using data through the prior session. Slippage and fees are simplified assumptions. No live market making, fills, or executable quotes.

**Strategy:** `{result.strategy}`

**Current observed regime (heuristic, not ML):** {regime['label']}

**Model validation warning:** This run does NOT constitute a held-out walk-forward predictive experiment or a trading performance claim. Compare to benchmark; investigate costs, alternative regimes and parameters.

## Performance

{summary.round(4).to_markdown() if _has_tabulate() else summary.round(4).to_string()}

## Out-of-sample historical VaR coverage

Forecast for session *t* uses the prior 252 trading sessions only. Results below are a risk model diagnostic, not evidence of predictive trading edge.

{coverage_stats}

## Hypothetical risk scenarios

{stress.round(4).to_markdown() if _has_tabulate() else stress.round(4).to_string()}

**Important:** Hypothetical shocks are user-configured scenarios, not historical or predictive scenarios. All risk metrics are backward-looking and do not bound future losses. If synthetic data were used, performance is illustrative ONLY.
"""
    (out / "research_report.md").write_text(note, encoding="utf-8")
    return {"strategy": strategy_metrics, "benchmark": base_metrics,
            "provenance": provenance, "regime": regime, "paths": str(out)}


def _has_tabulate() -> bool:
    try:
        import tabulate  # noqa: F401
        return True
    except ImportError:
        return False
