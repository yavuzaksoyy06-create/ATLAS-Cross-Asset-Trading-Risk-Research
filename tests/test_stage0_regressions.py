"""Stage 0 audit regressions: synthetic inputs, never market evidence."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from atlas.backtest import run_backtest
from atlas.data import price_returns, synthetic_prices
from atlas.desk import RiskLimits, decide_trade
from atlas.institutional_risk import exception_tests
from atlas.ml import make_features, walk_forward_downside
from atlas.real_study import historical_backtest
from atlas.risk import performance_stats


@pytest.fixture(scope="module")
def prices():
    return synthetic_prices(620, seed=12)


def test_drawdown_counts_initial_capital_loss():
    result = performance_stats(pd.Series([-.50] + [0.] * 39))
    assert result["max_drawdown"] == pytest.approx(-.50)


@pytest.mark.parametrize("cost", [np.nan, np.inf, -np.inf])
def test_backtest_rejects_nonfinite_costs(prices, cost):
    with pytest.raises(ValueError):
        run_backtest(price_returns(prices), "equal", fee_bps=cost)


@pytest.mark.parametrize("defect", ["reverse_dates", "duplicate_dates", "duplicate_assets"])
def test_backtest_requires_chronological_unique_panel(prices, defect):
    r = price_returns(prices)
    if defect == "reverse_dates":
        r = r.iloc[::-1]
    elif defect == "duplicate_dates":
        r.index = pd.DatetimeIndex([r.index[0]] * len(r))
    else:
        r.columns = ["SPY"] * r.shape[1]
    with pytest.raises(ValueError):
        run_backtest(r, "equal")


@pytest.mark.parametrize("defect", ["missing", "reverse_dates", "zero"])
def test_historical_engine_rejects_invalid_prices(prices, defect):
    p = prices[["SPY", "QQQ", "TLT"]].copy()
    if defect == "reverse_dates":
        p = p.iloc[::-1]
    else:
        p.iloc[80, 0] = np.nan if defect == "missing" else 0.
    with pytest.raises(ValueError):
        historical_backtest(p, "equal_3")


@pytest.mark.parametrize("parameter,value", [
    ("mid", np.nan), ("mid", np.inf), ("spread_bps", np.nan),
    ("spread_bps", -1.), ("nav_usd", np.inf),
])
def test_risk_gate_rejects_invalid_quote_inputs(prices, parameter, value):
    r = price_returns(prices)
    w = pd.Series(0., index=r.columns)
    w["SPY"], w["BIL"] = .5, .5
    args = dict(mid=100., ticker="SPY", side="buy", notional_usd=100.,
                nav_usd=1e6, assumed_adv_usd=1e8, spread_bps=4.)
    args[parameter] = value
    broad = RiskLimits(max_position_fraction=1., max_var95_usd=1e8,
                       max_stress_loss_usd=1e8, max_incremental_var95_usd=1e8)
    with pytest.raises(ValueError):
        decide_trade(w, r, limits=broad, **args)


def test_risk_gate_rejects_missing_returns(prices):
    r = price_returns(prices)
    # The desk deliberately assesses only the last 252 sessions.
    r.iloc[-3, 0] = np.nan
    w = pd.Series(0., index=r.columns)
    w["SPY"], w["BIL"] = .5, .5
    with pytest.raises(ValueError):
        decide_trade(w, r, 100., "SPY", "buy", 100., 1e6, 1e8)


@pytest.mark.parametrize("invalid", [np.full(40, .5), np.zeros((40, 2))])
def test_exception_tests_reject_nonbinary_or_multidimensional_data(invalid):
    with pytest.raises(ValueError):
        exception_tests(invalid)


def test_ml_rejects_reverse_dates(prices):
    with pytest.raises(ValueError):
        make_features(prices.iloc[::-1])


def test_ml_preserves_single_asset_feature_contract(prices):
    from atlas.data import validate_prices
    single = prices[["SPY"]]
    features, labels = make_features(single)
    full_features, full_labels = make_features(prices)
    pd.testing.assert_frame_equal(features, full_features[features.columns])
    pd.testing.assert_series_equal(labels, full_labels)
    # Portfolio ingestion still needs two assets; only ML opts into one.
    with pytest.raises(ValueError):
        validate_prices(single)


def test_ml_features_and_predictions_do_not_use_future_prices(prices):
    changed = prices.copy()
    changed.iloc[550:, 0] *= 1.7
    old_x, _ = make_features(prices)
    new_x, _ = make_features(changed)
    pd.testing.assert_frame_equal(old_x.iloc[:550], new_x.iloc[:550])
    before = walk_forward_downside(prices).predictions
    after = walk_forward_downside(changed).predictions
    # Outcomes near the mutation legitimately change; forecast probabilities must not.
    columns = ["probability", "expanding_base_rate"]
    cutoff = prices.index[550]
    pd.testing.assert_frame_equal(before.loc[before.index < cutoff, columns],
                                  after.loc[after.index < cutoff, columns])


def test_ml_label_is_forward_terminal_return_not_intrahorizon_drawdown():
    p = pd.DataFrame({"SPY": [100., 80., 100.], "TLT": [100., 100., 100.]},
                     index=pd.bdate_range("2020-01-01", periods=3))
    _, y = make_features(p, horizon=2, drawdown_threshold=-.03)
    assert y.iloc[0] == 0.  # Interim -20% is not a terminal loss event.
    assert y.iloc[-2:].isna().all()


def test_reference_rejects_nan_tolerance():
    from atlas.real_study import ARCHIVE_COMMIT, GIT_BLOBS
    from atlas.reference_validation import check_reference
    path = Path(__file__).resolve().parents[1] / "research/real_market_2018_2025/REFERENCE_RESULTS.json"
    reference = json.loads(path.read_text())
    summary = reference["results"]
    summary["60_40"]["2018_2025"]["annualized_return_pct"] += 100
    source = dict(data_category="HISTORICAL_ARCHIVED_ETF_CLOSES_NOT_SYNTHETIC",
                  pinned_repository_commit=ARCHIVE_COMMIT, git_blob_sha1=GIT_BLOBS,
                  observations=2011)
    with pytest.raises(ValueError):
        check_reference(summary, source, path, tolerance_percentage_points=np.nan)


def test_repeated_publication_manifest_never_hashes_itself(tmp_path):
    from atlas.institutional_report import investigate, publish
    rng = np.random.default_rng(911)
    p = pd.DataFrame(100 * np.exp(np.cumsum(rng.normal(0, .01, (850, 3)), axis=0)),
                     index=pd.bdate_range("2020-01-01", periods=850),
                     columns=["SPY", "QQQ", "TLT"])
    study = investigate(p, bootstrap_repetitions=100, risk_window=85)
    source = {"data_category": "SYNTHETIC_TEST_FIXTURE"}
    first = publish(study, tmp_path, source, include_plotly=False)
    second = publish(study, tmp_path, source, include_plotly=False)
    assert "OUTPUT_SHA256.json" not in second
    assert first == second
