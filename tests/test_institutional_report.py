"""Adversarial tests for publication-grade analysis; synthetic fixtures only."""
import json
import numpy as np
import pandas as pd
import pytest
from atlas.institutional_report import costed_buy_hold, investigate, publish
from atlas.real_study import historical_backtest
from atlas.institutional_risk import exception_tests, rolling_risk_validation
from atlas.historical_events import replay_event_windows
from atlas.research_qa import audit_prices


def fake_prices(n=820):
    # A fixture is deliberately not historical market data.
    dates = pd.bdate_range('2020-01-01', periods=n)
    rng = np.random.default_rng(911)
    x = rng.normal(loc=[.0003, .0004, .00015], scale=[.010, .015, .008], size=(n,3))
    px = 100*np.exp(np.cumsum(x,axis=0))
    return pd.DataFrame(px,index=dates,columns=['SPY','QQQ','TLT'])


def test_buy_hold_initial_cost_only_and_shifted_index():
    p = pd.Series([100., 110., 121.],index=pd.bdate_range('2020-01-01',periods=3))
    x = costed_buy_hold(p,.001)
    np.testing.assert_allclose(x.to_numpy(),[(1-.001)*1.1-1,.1])
    assert len(x) == 2
    with pytest.raises(ValueError):
        costed_buy_hold(p,-.2)


def test_historical_events_expost_and_well_labeled():
    x=pd.DataFrame({'portfolio':[.01,-.1,.04,.02]},index=pd.bdate_range('2020-03-16',periods=4))
    events={'Sample':('2020-03-16','2020-03-19')}
    ans=replay_event_windows(x,events)
    assert ans.iloc[0]['sessions']==4
    assert ans.iloc[0]['worst_session']==-.1
    assert abs(ans.iloc[0]['cumulative_return']-np.prod(1+x['portfolio'])+1) < 1e-12
    with pytest.raises(ValueError):
        replay_event_windows(x,{'Bad':('2021-01-01','2020-01-01')})


def test_exception_independence_and_past_only_coverage():
    seq = np.zeros(130, dtype=int)
    seq[::21]=1
    x=exception_tests(seq,confidence=.95)
    assert x['observations']==130 and x['breaches']==7
    assert 0 <= x['kupiec_pvalue'] <= 1
    s=pd.Series(np.random.default_rng(8).normal(0,.01,410),index=pd.bdate_range('2020-01-01',periods=410))
    a=rolling_risk_validation(s,window=75,confidence=.95)
    z=s.copy(); z.iloc[-1]=-.5
    b=rolling_risk_validation(z,window=75,confidence=.95)
    np.testing.assert_allclose(a.forecasts[['var_historical','var_ewma_gaussian']].to_numpy(),
                               b.forecasts[['var_historical','var_ewma_gaussian']].to_numpy())
    assert b.forecasts['breach_historical'].iloc[-1]==1


def test_data_quality_rejects_corruption():
    p=fake_prices()
    assert audit_prices(p)['observations']==len(p)
    p.iloc[1,0]=np.nan
    with pytest.raises(ValueError):
        audit_prices(p)


def test_live_publication_pipeline_with_explicit_synthetic_fixture(tmp_path):
    p=fake_prices(870)
    result=investigate(p,bootstrap_repetitions=100,risk_window=85,risk_confidence=.95)
    assert len(result.daily)==len(p)-1
    assert result.methodology['no_untouched_test_claim'] is True
    assert set(['SPY_buy_hold_net','SPY_benchmark_no_cost','60_40','equal_3','inverse_vol_63']).issubset(result.daily.columns)
    assert result.coverage['breaches'].ge(0).all()
    assert result.performance.loc['reviewed_2023_2025'].shape[0]==5
    publish(result,tmp_path,provenance={'origin_archive':'SYNTHETIC TEST ONLY'},include_plotly=False)
    assert (tmp_path/'EMPIRICAL_RESEARCH_MEMO.md').exists()
    assert 'SYNTHETIC TEST ONLY' in (tmp_path/'EMPIRICAL_RESEARCH_MEMO.md').read_text()
    assert (tmp_path/'OUTPUT_SHA256.json').exists()
    z=json.loads((tmp_path/'reproduction_manifest.json').read_text())
    assert z['methodology']['portfolio_rebalance_sessions']==21
    assert len(result.cost_sensitivity)==5*3*2
    # Plain SPY passively held is at most one initial purchase, not billed monthly.
    assert result.daily['SPY_buy_hold_net'].iloc[1]==pytest.approx(result.daily['SPY_benchmark_no_cost'].iloc[1])
    assert result.daily['SPY_buy_hold_net'].iloc[0]<result.daily['SPY_benchmark_no_cost'].iloc[0]
