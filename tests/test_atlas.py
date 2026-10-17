import numpy as np
import pandas as pd
import pytest
from atlas.data import synthetic_prices, price_returns
from atlas.backtest import run_backtest
from atlas.risk import historical_var_es, performance_stats, stress_portfolio, risk_contributions, var_coverage_backtest
from atlas.strategies import STRATEGIES
from atlas.rfq import simulate_rfq

@pytest.fixture(scope="module")
def panel():
    p = synthetic_prices(460, seed=7)
    return p, price_returns(p)


def test_synthetic_reproducible(panel):
    prices, returns = panel
    pd.testing.assert_frame_equal(prices, synthetic_prices(460, seed=7))
    assert returns.notna().all().all()


@pytest.mark.parametrize("strategy", list(STRATEGIES))
def test_strategy_weights_normalized(panel, strategy):
    _, r = panel
    bt = run_backtest(r, strategy=strategy)
    assert np.allclose(bt.weights.sum(axis=1), 1)
    assert (bt.weights >= 0).all().all()
    assert bt.equity.min() > 0
    assert (bt.turnover >= 0).all()


def test_no_future_leakage(panel):
    _, r = panel
    modified = r.copy()
    modified.iloc[380:, modified.columns.get_loc("SPY")] = -.30
    old = run_backtest(r, strategy="regime")
    new = run_backtest(modified, strategy="regime")
    pd.testing.assert_frame_equal(old.weights.iloc[:380], new.weights.iloc[:380])
    pd.testing.assert_series_equal(old.daily_returns.iloc[:380], new.daily_returns.iloc[:380])


def test_costs_reduce_results(panel):
    _, r = panel
    free = run_backtest(r, strategy="momentum", fee_bps=0, slippage_bps=0)
    costly = run_backtest(r, strategy="momentum", fee_bps=10, slippage_bps=15)
    assert costly.equity.iloc[-1] < free.equity.iloc[-1]
    assert costly.costs.sum() > 0


def test_var_expected_shortfall_as_losses():
    sample = pd.Series([-0.11, -0.08, -0.04] + [0.001]*100)
    var, es = historical_var_es(sample)
    assert 0 <= var <= es
    assert es > 0


def test_stress_and_risk_contributions(panel):
    _, r = panel
    w = pd.Series({t: 1/len(r.columns) for t in r.columns})
    result = stress_portfolio(w)
    assert result.shape == (3, 2)
    rc = risk_contributions(r, w)
    assert np.isclose(rc.vol_contribution_share.sum(), 1.0)


def test_rfq_rejects_unfunded_trade(panel):
    prices, r = panel
    w = pd.Series(0.0, index=r.columns)
    w["SPY"], w["BIL"] = .50, .50
    quote = simulate_rfq(w, r, latest_mid=float(prices["SPY"].iloc[-1]),
                         ticker="SPY", side="sell", notional_usd=20_000)
    assert quote.updated_weights["SPY"] < w["SPY"]
    assert quote.updated_weights.sum() == pytest.approx(1)
    assert quote.before_var95_usd >= 0
    assert quote.after_var95_usd >= 0
    with pytest.raises(ValueError):
        simulate_rfq(w, r, latest_mid=100, ticker="SPY", side="sell", notional_usd=600_000)


def test_stats_are_finite(panel):
    _, r = panel
    stats = performance_stats(r["SPY"])
    assert np.isfinite(stats["annualized_return"])
    assert stats["max_drawdown"] <= 0


def test_cvar_optimizer_constraints(panel):
    from atlas.optimization import min_cvar_weights
    _, r = panel
    w = min_cvar_weights(r, lookback=252)
    assert w.sum() == pytest.approx(1.0)
    assert (w >= -1e-8).all()
    assert (w <= .350001).all()


def test_var_backtest_no_future_leakage(panel):
    _, r = panel
    original = r["SPY"]
    altered = original.copy()
    altered.iloc[-20:] = -.35
    prior, stats = var_coverage_backtest(original, lookback=252)
    future, future_stats = var_coverage_backtest(altered, lookback=252)
    pd.testing.assert_frame_equal(prior.iloc[:-20], future.iloc[:-20])
    assert stats["observations"] == future_stats["observations"]


def test_ml_purged_training_and_probabilities():
    from atlas.ml import walk_forward_downside
    p = synthetic_prices(600, seed=12)
    ml = walk_forward_downside(p)
    assert len(ml.predictions) >= 30
    assert ml.predictions.probability.between(0, 1).all()
    assert np.isfinite(ml.brier_model)
    assert np.isfinite(ml.brier_baseline)
