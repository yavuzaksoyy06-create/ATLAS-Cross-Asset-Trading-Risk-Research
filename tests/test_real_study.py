import io
import json
import numpy as np
import pandas as pd
import pytest
from atlas.real_study import (blob_sha1, parse_archive_csv, archive_url,
    make_targets, historical_backtest, strategy_summary, run_study)


def fixture_prices(n=420, start='2018-01-02'):
    dates = pd.bdate_range(start, periods=n)
    rng = np.random.default_rng(103)
    logreturns = rng.normal(0, [0.012, 0.016, 0.007], (n, 3))
    prices = 100*np.exp(np.cumsum(logreturns, axis=0))
    return pd.DataFrame(prices, index=dates, columns=['SPY','QQQ','TLT'])


def test_parse_and_checksum():
    raw = b'Date,Close\n2018-01-02,100\n2018-01-03,101\n'
    assert len(blob_sha1(raw)) == 40
    parsed = parse_archive_csv(raw, 'SPY')
    assert len(parsed) == 2 and parsed.iloc[-1] == 101
    with pytest.raises(ValueError):
        parse_archive_csv(b'Date,Close\n2018-01-02,-2\n', 'SPY')
    assert '7d9d769b0' in archive_url('SPY')


def test_weight_constraints_and_no_current_day_leak():
    p = fixture_prices()
    a = historical_backtest(p, 'inverse_vol_63')
    q = p.copy()
    # Changing a distant future return MUST NOT change a past target/return.
    q.iloc[-1, 1] *= 2
    b = historical_backtest(q, 'inverse_vol_63')
    np.testing.assert_allclose(a.iloc[:-1], b.iloc[:-1], atol=1e-12)
    for name in ['60_40','equal_3','inverse_vol_63']:
        w = make_targets(np.ones((90,3))*.001, name)
        assert abs(w.sum()-1) < 1e-12
        assert min(w) >= 0


def test_cost_monotonic_at_first_rebalance():
    p = fixture_prices()
    low = historical_backtest(p, 'equal_3', cost=0.0)
    high = historical_backtest(p, 'equal_3', cost=0.0008)
    assert low.iloc[0] > high.iloc[0]


def test_real_study_summary_and_date_alignment():
    p = fixture_prices(start='2022-01-03')
    daily, s = run_study(p)
    assert len(daily) == len(p)-1
    assert daily.notna().all().all()
    assert len(s) == 4
    assert strategy_summary(daily.iloc[:, 0])['annualized_volatility_pct'] > 0


def test_no_bogus_results():
    with pytest.raises(ValueError):
        strategy_summary(pd.Series([float('nan')] * 35))
    with pytest.raises(ValueError):
        archive_url('FAKE')
