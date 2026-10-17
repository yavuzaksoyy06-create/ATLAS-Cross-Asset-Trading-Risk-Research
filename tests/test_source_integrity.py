"""Research provenance must survive publication and rule out disguised synthetic alpha."""
import json
import numpy as np
import pandas as pd
from atlas.research_labels import source_kind, is_pinned
from atlas.real_study import run_study, write_study
from atlas.institutional_report import investigate, publish


def fake_prices():
    dates = pd.bdate_range('2020-01-01', periods=850)
    rng = np.random.default_rng(629)
    increments = rng.normal(0, [0.01, .015, .007], (850, 3))
    return pd.DataFrame(100 * np.exp(np.cumsum(increments, axis=0)),
                        index=dates, columns=['SPY', 'QQQ', 'TLT'])


def test_source_classifier_rejects_unverified_escalation():
    assert 'UNVERIFIED' in source_kind({'data_category': 'USER_SUPPLIED_UNVERIFIED_ADJUSTED_PRICE_CLAIM'})
    assert 'SYNTHETIC' in source_kind({'origin_archive': 'SYNTHETIC TEST ONLY'})
    assert not is_pinned({'data_category': 'SYNTHETIC_TEST_FIXTURE'})
    assert is_pinned({'data_category': 'HISTORICAL_ARCHIVED_ETF_CLOSES_NOT_SYNTHETIC'})


def test_synthetic_write_study_never_claims_verified_history(tmp_path):
    prices = fake_prices()
    daily, metrics = run_study(prices)
    metadata = {'data_category': 'SYNTHETIC_TEST_FIXTURE', 'origin_archive': 'GENERATED DEMO'}
    write_study(tmp_path, daily, metrics, metadata)
    text = (tmp_path / 'CASE_STUDY.md').read_text()
    assert 'SYNTHETIC' in text
    assert '2018-01-02 through 2025-12-31' not in text
    assert 'verified market evidence' in text
    result = json.loads((tmp_path / 'result.json').read_text())
    assert 'SYNTHETIC' in result['research_parameters']['source_classification']
    assert result['research_parameters']['dates'][0] == str(daily.index.min().date())


def test_synthetic_research_report_exports_preserve_label(tmp_path):
    prices = fake_prices()
    data = investigate(prices, bootstrap_repetitions=100, risk_window=90, risk_confidence=.95)
    source = {'data_category': 'SYNTHETIC_TEST_FIXTURE', 'origin_archive': 'GENERATED DEMO'}
    publish(data, tmp_path, source, include_plotly=False)
    text = (tmp_path / 'EMPIRICAL_RESEARCH_MEMO.md').read_text()
    assert 'SYNTHETIC ENGINEERING FIXTURE' in text
    assert 'NOT VERIFIED HISTORICAL EVENTS' in text
    assert 'Input-Panel' not in text  # memo uses explicitly disclaimed engineering title
    table = pd.read_csv(tmp_path / 'performance_summary.csv')
    assert table['dataset_classification'].str.contains('SYNTHETIC').all()
