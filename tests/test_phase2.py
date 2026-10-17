"""Independent adversarial checks for v0.2 source, holdout and trade gating."""
import json
import numpy as np
import pandas as pd
import pytest
from atlas.data import synthetic_prices, price_returns
from atlas.provenance import snapshot_prices, verify_snapshot
from atlas.evaluation import paired_block_bootstrap, evaluate_fixed_strategies, write_evaluation
from atlas.desk import RiskLimits, decide_trade, write_decision_memo


@pytest.fixture(scope="module")
def demo():
    prices = synthetic_prices(560, seed=21)
    return prices, price_returns(prices)


def test_snapshot_roundtrip_and_tamper(tmp_path, demo):
    prices, _ = demo
    manifest = snapshot_prices(prices, "SYNTHETIC test", tmp_path)
    verified, recorded = verify_snapshot(tmp_path)
    pd.testing.assert_frame_equal(prices, verified, check_exact=False, check_freq=False, rtol=1e-14)
    assert recorded["sha256"] == manifest["sha256"]
    assert recorded["data_label"].startswith("SYNTHETIC")
    path = tmp_path / "adjusted_prices_snapshot.csv"
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="SHA256"):
        verify_snapshot(tmp_path)


def test_snapshot_rejects_corrupt_prices(tmp_path, demo):
    prices, _ = demo
    prices.iloc[4, 2] = np.nan
    with pytest.raises(ValueError):
        snapshot_prices(prices, "UNKNOWN", tmp_path)


def test_bootstrap_seed_and_null():
    x = pd.Series([0.0] * 155)
    a = paired_block_bootstrap(x, repetitions=120)
    assert a == (0., 0.)
    assert a == paired_block_bootstrap(x, repetitions=120)
    with pytest.raises(ValueError):
        paired_block_bootstrap(x, block_size=200)


def test_evaluation_uses_exact_fixed_split_and_outputs(tmp_path, demo):
    _, ret = demo
    start = str(ret.index[420].date())
    ans = evaluate_fixed_strategies(ret, start, strategies=("equal", "momentum"),
                                    repetitions=100, seed=99)
    assert ans.methodology["training_sessions"] == 420
    assert ans.methodology["test_sessions"] == len(ret) - 420
    assert ans.daily_holdout.index[0] == ret.index[420]
    assert (ans.summary["sessions"] == len(ret) - 420).all()
    assert ans.summary["bootstrap_95ci_excess_mean_low"].le(ans.summary["bootstrap_95ci_excess_mean_high"]).all()
    write_evaluation(ans, tmp_path)
    assert (tmp_path / "evaluation_methodology.json").exists()
    m = json.loads((tmp_path / "evaluation_methodology.json").read_text())
    assert "not a fitted" in m["study"]


def test_evaluation_no_peeking_into_future_prices(demo):
    _, ret = demo
    change = ret.copy()
    change.loc[change.index[500]:, "SPY"] = -.20
    before = evaluate_fixed_strategies(ret, str(ret.index[450].date()),
                                       strategies=("regime",), repetitions=100)
    after = evaluate_fixed_strategies(change, str(ret.index[450].date()),
                                      strategies=("regime",), repetitions=100)
    pd.testing.assert_series_equal(before.daily_holdout["regime"].iloc[:50],
                                   after.daily_holdout["regime"].iloc[:50])


def test_evaluation_cost_sensitivity(demo):
    _, ret = demo
    args = {"test_start": str(ret.index[400].date()), "strategies": ("momentum",),
            "repetitions": 100}
    no_cost = evaluate_fixed_strategies(ret, **args, fee_bps=0, slippage_bps=0)
    costly = evaluate_fixed_strategies(ret, **args, fee_bps=10, slippage_bps=30)
    assert costly.summary.loc["momentum", "total_return_net"] < no_cost.summary.loc["momentum", "total_return_net"]


def test_decision_gate_pass_and_fail(tmp_path, demo):
    prices, returns = demo
    w = pd.Series(0., index=returns.columns)
    w["SPY"], w["BIL"] = .50, .50
    broad = RiskLimits(max_position_fraction=.95, max_var95_usd=1e8,
                       max_stress_loss_usd=1e8, max_daily_adv_participation=1,
                       max_incremental_var95_usd=1e8)
    d, _ = decide_trade(w, returns, float(prices["SPY"].iloc[-1]), "SPY", "buy",
                        20_000, 1e6, 5e6, broad)
    assert d.decision == "PASS_DEMO_LIMITS"
    strict = RiskLimits(max_position_fraction=.50, max_var95_usd=1,
                        max_stress_loss_usd=1, max_daily_adv_participation=.001,
                        max_incremental_var95_usd=0)
    rejected, _ = decide_trade(w, returns, float(prices["SPY"].iloc[-1]), "SPY", "buy",
                               20_000, 1e6, 5e6, strict)
    assert rejected.decision == "REJECT"
    assert any("ADV_PARTICIPATION_LIMIT:" in r for r in rejected.reasons)
    path = tmp_path / "memo"
    write_decision_memo(rejected, strict, path, "SYNTHETIC", "2026-10-16")
    assert (tmp_path / "memo.md").exists()
    assert json.loads((tmp_path / "memo.json").read_text())["decision"]["decision"] == "REJECT"


def test_unfunded_trade_is_rejected(demo):
    prices, returns = demo
    w = pd.Series(0., index=returns.columns)
    w["SPY"], w["BIL"] = .99, .01
    with pytest.raises(ValueError, match="Insufficient"):
        decide_trade(w, returns, float(prices["SPY"].iloc[-1]), "SPY", "buy",
                     50_000, 1e6, 5e6)
