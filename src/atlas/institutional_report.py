"""Publication-grade, explicitly exploratory historical ETF desk case study.

Input prices must be verified by caller, preferably via the pinned data downloader.
This is NOT a live trading system, licensed data feed, or independent alpha proof.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd

from .evaluation import paired_block_bootstrap
from .historical_events import replay_event_windows
from .institutional_risk import rolling_risk_validation
from .real_study import (SYMBOLS, TEST_START, TRADING_COST_PER_ONE_WAY_TURNOVER,
                         historical_backtest, run_study, strategy_summary)
from .research_qa import audit_prices
from .research_labels import source_kind, is_pinned


@dataclass
class InstitutionalStudy:
    daily: pd.DataFrame
    performance: pd.DataFrame
    crises: pd.DataFrame
    cost_sensitivity: pd.DataFrame
    coverage: pd.DataFrame
    risk_forecasts: pd.DataFrame
    uncertainty: pd.DataFrame
    dataset_quality: dict
    methodology: dict


def costed_buy_hold(prices: pd.Series, one_way_cost: float = TRADING_COST_PER_ONE_WAY_TURNOVER) -> pd.Series:
    """Start fully in cash, buy at the first available close-to-close period.

    Charge one purchase and then hold. There is no liquidation fee at the end.
    Adjusted closes approximate total return only if upstream adjustment is correct.
    """
    p = prices.to_numpy(dtype=float)
    if len(p) < 2 or not 0 <= one_way_cost < 1 or not np.isfinite(p).all() or np.any(p <= 0):
        raise ValueError('Positive historical prices and valid cost fraction required.')
    returns = p[1:] / p[:-1] - 1
    returns[0] = (1 - one_way_cost) * (1 + returns[0]) - 1
    return pd.Series(returns, index=prices.index[1:], name='SPY_buy_hold_net')


def _full_metrics(series: pd.Series) -> dict:
    return strategy_summary(series)


def investigate(prices: pd.DataFrame, bootstrap_repetitions: int = 500,
                risk_window: int = 252, risk_confidence: float = .99) -> InstitutionalStudy:
    """Compute held-in-time simulations, never market-data-inferred economic causality.

    *Trade signal at t only sees returns up to t-1.* Data rules are established
    before each run; but the entire 2018-2025 sample has already been reviewed.
    No untouched out-of-sample claim is permissible.
    """
    if list(prices.columns) != list(SYMBOLS):
        raise ValueError(f'Expected exactly {SYMBOLS} in reproducible order')
    qa = audit_prices(prices)
    if len(prices) < 400 or prices.index[0] >= pd.Timestamp(TEST_START) or prices.index[-1] < pd.Timestamp(TEST_START):
        raise ValueError('Need pre-2023 training history and a 2023+ comparison segment')
    if bootstrap_repetitions < 100:
        raise ValueError('Bootstrap needs at least 100 draws')
    past, _ = run_study(prices)
    daily = past.copy()
    daily.insert(0, 'SPY_buy_hold_net', costed_buy_hold(prices['SPY']))

    # The index is already entirely in the past by the time of this ex-post study.
    periods = {'full_2018_2025': daily, 'reviewed_2023_2025': daily.loc[TEST_START:]}
    metric_rows = []
    for period, frame in periods.items():
        for asset in frame:
            metric_rows.append({'period': period, 'strategy': asset, **_full_metrics(frame[asset])})
    performance = pd.DataFrame.from_records(metric_rows).set_index(['period', 'strategy'])

    crises = replay_event_windows(daily)
    sweep_rows = []
    for bps in (0, 4, 8, 15, 30):
        cost = bps / 10_000
        for label in ('60_40', 'equal_3', 'inverse_vol_63'):
            r = historical_backtest(prices, label, cost=cost)
            for segment, ser in (('full_2018_2025', r), ('reviewed_2023_2025', r.loc[TEST_START:])):
                s = strategy_summary(ser)
                sweep_rows.append({'one_way_cost_bps': bps, 'strategy': label, 'period': segment,
                    'cagr_pct': s['annualized_return_pct'], 'max_drawdown_pct': s['max_drawdown_pct'],
                    'cumulative_return_pct': s['cumulative_return_pct']})
    sensitivity = pd.DataFrame.from_records(sweep_rows)

    risk_rows = []
    forecast_frames = []
    for asset in daily.columns:
        result = rolling_risk_validation(daily[asset], window=risk_window,
                                         confidence=risk_confidence)
        for model, row in result.diagnostics.iterrows():
            risk_rows.append({'strategy': asset, 'model': model,
                **{k: v for k, v in row.to_dict().items() if k not in {'transitions'}}})
        frame = result.forecasts.copy()
        frame.insert(0, 'strategy', asset)
        forecast_frames.append(frame.reset_index())
    risk_tests = pd.DataFrame.from_records(risk_rows)
    forecast_panel = pd.concat(forecast_frames, ignore_index=True)

    # Compare paired contemporaneous strategy daily returns to costed SPY.
    # Bootstrap interval: *annualized arithmetic difference*, NOT excess CAGR.
    uncertainty_rows = []
    for period, frame in periods.items():
        for i, strategy in enumerate(('60_40', 'equal_3', 'inverse_vol_63')):
            differences = frame[strategy] - frame['SPY_buy_hold_net']
            lo, hi = paired_block_bootstrap(differences,
                block_size=min(21, len(differences)), repetitions=bootstrap_repetitions, seed=1701+i)
            uncertainty_rows.append({'period': period, 'strategy': strategy,
                'benchmark': 'SPY_buy_hold_net', 'annualized_arithmetic_mean_excess':
                    float(differences.mean()*252), 'bootstrap_95ci_low': lo, 'bootstrap_95ci_high': hi,
                'block_length_sessions': min(21, len(differences)),
                'resamples': bootstrap_repetitions,
                'interval_is_exploratory': True})
    uncertainty = pd.DataFrame(uncertainty_rows)

    methodology = {
        'study_type': 'retrospective_exploratory_non_preregistered',
        'no_untouched_test_claim': True,
        'historical_observations': len(prices), 'return_observations': len(daily),
        'first_observation': str(prices.index.min().date()),
        'last_observation': str(prices.index.max().date()),
        'reviewed_segment_starts': TEST_START, 'assets': list(SYMBOLS),
        'allocation_rules': ['60_40', 'equal_3', 'inverse_vol_63'],
        'portfolio_rebalance_sessions': 21,
        'one_way_turnover_cost_bps': 8,
        'buy_and_hold_initial_purchase_cost_bps': 8,
        'benchmark_cost_method': 'Charge single initial SPY buy; no end liquidation fee',
        'other_benchmark': 'SPY_benchmark_no_cost retained solely for continuity and transparency',
        'bootstrap_meaning': 'circular paired-block CI for annualized arithmetic mean daily excess',
        'bootstrap_multiple_comparisons_warning': 'Three comparisons; unadjusted intervals are exploratory',
        'risk_backtest': {'window_sessions': risk_window,
            'confidence': risk_confidence, 'models': ['historical_simulation', 'zero_mean_Gaussian_EWMA'],
            'coverage_tests': ['Kupiec LRuc', 'Christoffersen LRind', 'LRcc'],
            'warning': 'Large-sample chi-square p-values have low power at 99% with few breaches'},
        'risk_free_rate_assumption': 0.0,
        'backtest_timing': 'Allocation at t uses price changes ending at t-1 or earlier',
        'crisis_labels': 'Ex-post date windows; only genuine historical market events for a verified archive input, otherwise calendar-window engineering checks',
        'market_data': ('Third-party archive claims prices adjusted for splits/dividends;'
                        ' not independently audited and may be subject to redistribution restrictions'),
        'execution': 'Daily close-to-close approximation; assumed commission+slippage, not executed fills',
        'research_limits': ['hindsight ETF asset universe','look-ahead-free algorithm does not make selection point-in-time',
            'no financing/borrow/taxes/cash return','no order book or real ADV',
            'observed results do not imply predictive success','source vendor rights not independently verified'],
    }
    return InstitutionalStudy(daily, performance, crises, sensitivity, risk_tests,
                              forecast_panel, uncertainty, qa, methodology)


def _markdown_table(df: pd.DataFrame, cols: list[str], fmt=None) -> str:
    d = df.loc[:, cols].reset_index(drop=True).copy()
    if fmt:
        for name in cols:
            if name in fmt:
                d[name] = d[name].map(fmt[name])
    header = '| ' + ' | '.join(cols) + ' |'
    sep = '|' + '|'.join('---' for _ in cols) + '|'
    rows = ['| ' + ' | '.join(str(value) for value in rec) + ' |' for rec in d.itertuples(index=False, name=None)]
    return '\n'.join([header, sep, *rows])


def publish(study: InstitutionalStudy, target: str | Path, provenance: dict,
            include_plotly: bool = True) -> dict:
    """Write research-derived aggregates only; never redistribute provider raw prices."""
    out = Path(target)
    out.mkdir(parents=True, exist_ok=True)
    classification = source_kind(provenance)
    frames = {
        'performance_summary.csv': study.performance.reset_index(),
        'historical_stress_windows.csv': study.crises,
        'cost_sensitivity.csv': study.cost_sensitivity,
        'risk_model_diagnostics.csv': study.coverage,
        'uncertainty_intervals.csv': study.uncertainty,
    }
    for fname, df in frames.items():
        exported = df.copy()
        if 'period' in exported.columns:
            exported['period'] = exported['period'].replace({
                'full_2018_2025':'full_observed_panel',
                'reviewed_2023_2025':'reviewed_post_2023_panel'})
        exported.insert(0, 'panel_last_observation', study.methodology['last_observation'])
        exported.insert(0, 'panel_first_observation', study.methodology['first_observation'])
        exported.insert(0, 'dataset_classification', classification)
        exported.to_csv(out / fname, index=False, float_format='%.12g')
    # Forecast-level derived series are not raw OHLCV but may reproduce approximate
    # historical returns. Do not publish this by default without checking rights.
    parameters = {'source': provenance, 'methodology': study.methodology,
                  'data_quality': study.dataset_quality,
                  'outputs': sorted(frames),
                  'disclosure': 'Research results only; no raw vendor price archive distributed.'}
    (out / 'reproduction_manifest.json').write_text(json.dumps(parameters, indent=2, default=str), encoding='utf-8')

    perf = (study.performance.loc['reviewed_2023_2025']
            .reset_index()[['strategy','annualized_return_pct','annualized_volatility_pct',
                            'max_drawdown_pct','historical_es_95_daily_loss_pct']])
    show = perf.copy()
    def pct(v): return f'{v:+.2f}%'
    table = _markdown_table(show,
        ['strategy', 'annualized_return_pct', 'annualized_volatility_pct',
         'max_drawdown_pct', 'historical_es_95_daily_loss_pct'],
        {c: pct for c in show.columns if c != 'strategy'})
    sub_crises = study.crises[study.crises['asset_or_strategy'].isin(('SPY_buy_hold_net', '60_40','equal_3','inverse_vol_63'))]
    c = sub_crises[['event','asset_or_strategy','cumulative_return']].copy()
    c['cumulative_return'] *= 100
    crisis_table = _markdown_table(c,['event','asset_or_strategy','cumulative_return'],
                                   {'cumulative_return':pct})
    lower = study.uncertainty[study.uncertainty['period']=='reviewed_2023_2025'].copy()
    for name in ['annualized_arithmetic_mean_excess','bootstrap_95ci_low','bootstrap_95ci_high']:
        lower[name] *= 100
    intervals = _markdown_table(lower, ['strategy','annualized_arithmetic_mean_excess',
                          'bootstrap_95ci_low','bootstrap_95ci_high'],
        {c:pct for c in ('annualized_arithmetic_mean_excess','bootstrap_95ci_low','bootstrap_95ci_high')})
    diagnostic = study.coverage[['strategy','model','observations','breaches','expected_breaches',
                    'kupiec_pvalue','christoffersen_coverage_pvalue']].copy()
    # 99% VaR coverage failures are not equivalent to standalone model rejection at 5%.
    diag_table = _markdown_table(diagnostic, list(diagnostic.columns),
        {c: (lambda v: f'{v:.3f}') for c in ['expected_breaches','kupiec_pvalue','christoffersen_coverage_pvalue']})
    source_url = provenance.get('origin_archive','Unspecified supplied market-data source')
    verified_snapshot = is_pinned(provenance)
    heading = ('Empirical Research Memo — Third-party Archive' if verified_snapshot
               else 'Engineering Research Memo — UNVERIFIED / SYNTHETIC INPUT')
    window_label = ('Historical realized windows (ex-post labelled)' if verified_snapshot
                    else 'Date-window engineering replay — NOT VERIFIED HISTORICAL EVENTS')
    dataset_sentence = ('the vendor\'s *unverified* adjusted-close claim' if verified_snapshot
                        else 'an unverified/synthetic input panel, not observed market evidence')
    report = f'''# ATLAS | Cross-Asset Trading Desk — {heading}

> **DATASET CLASSIFICATION: {classification}**

> **Research status: RETROSPECTIVE / EXPLORATORY.** Published for engineering and quantitative-method transparency, NOT demonstrated alpha, investment advice, actual desk execution or bank affiliation.

## Executive decision

An interpretable portfolio risk engine compared three long-only ETF allocation rules against a passive S&P 500 ETF reference across **{len(study.daily):,} aligned daily returns**. The review covered **{study.methodology['first_observation']}–{study.methodology['last_observation']}** and considered a previously viewed period **beginning 2023-01-03** (ending with the panel's last date). The latter **is not an untouched out-of-sample holdout**. Performance is conditional on {dataset_sentence} and simplified execution assumptions.

## How the study is designed

- Instruments: SPY (US equity proxy), QQQ (Nasdaq-100 equity proxy), TLT (long-duration US Treasury ETF proxy). These are ETFs, not a complete market-making cross-asset inventory.
- Strategies: fixed 60/40 SPY/TLT, three-asset equal weight, or three-asset 63-session inverse volatility, all long-only and fully invested.
- Decisions use *past* returns. Portfolios rebalance every 21 observed sessions; NAV, shares, and weights drift between rebalances.
- Fee and slippage assumption: **8 basis points per one-way absolute turnover**, including startup purchases. Passive SPY is also assessed an initial **8 basis point purchase** in the fairer benchmark `SPY_buy_hold_net`; the older uncosted benchmark remains visible for comparison.
- Annualized volatility is daily sample volatility times √252; Sharpe uses a **0% risk-free-rate assumption**, not an actual cash yield.
- Interval estimates: paired circular 21-session block bootstrap for annualized *arithmetic mean daily* differences; multiple-testing and non-stationarity are **not solved** by these intervals.

## Results: previously reviewed post-2023 interval (available data only)

{table}

**Interpretation:** Lower maximum drawdown may come with lower returns; a strategy is not automatically superior because it diversifies. For a true apples-to-apples investment comparison, further research must incorporate cash yields, tax, implementation and market-wide investability. These reported rules were not independently optimized or preregistered before all outcomes were inspected.

## Incremental value vs. costed passive SPY

{intervals}

A confidence interval covering zero does not demonstrate outperformance. One excluding zero is still *exploratory*, given strategy selection, finite sample, and multiple comparisons.

## {window_label}

{crisis_table}

These are simulated portfolio NAV replays within the selected date windows, **not proof that the input was a historical market series**. On a pinned archive they are ex-post realized historical-price proxy windows; on a synthetic or unverified panel they are engineering checks, not crisis evidence. Window dates were selected with hindsight. Turnover and assumed costs remain in portfolio daily returns.

## Risk calibration, 99% daily VaR

{diag_table}

Each day's VaR used **only the previous {study.methodology['risk_backtest']['window_sessions']} sessions**. Coverage diagnostics include Kupiec unconditional coverage and Christoffersen independence/conditional coverage. The asymptotic p-values have low power when 99% tail events are rare and cannot certify a model's safety, validity for regulatory capital or resilience under future regime changes.

## Trading-cost robustness

`cost_sensitivity.csv` reruns portfolio allocations across assumed one-way turnover costs of 0, 4, 8, 15, and 30 bps (no fee estimation from historical trades). Inference must be stress-tested across realistic spreads, liquidity and turnover; this table is a *sensitivity analysis*, not measured historical execution cost.

## Dataset provenance and reproducibility

- Pinned source: {source_url}
- Dataset classification: **{classification}**. Git blob checks apply ONLY to pinned third-party archives; they are NOT performed on synthetic or user CSV uploads.
- Complete provider OHLCV files are **not redistributed** with ATLAS. Their licensing and corporate-action accuracy have **not been independently validated**.
- Steps: `pip install -e '.[all]'` then `python -m atlas.real_study --output results/real_market` on a computer with network access.
- The third-party pinned source is not live pricing or 2026 prices. User CSV and synthetic fixtures have no verified-vendor provenance. Reproducing pinned history requires the external repository to be accessible.

## Disclosures and key failure modes

1. Current selection of survivor ETFs introduces hindsight/universe selection bias; this is not a historical point-in-time security universe.
2. Close-to-close trading and a constant 8 bps are approximate; an actual trading desk must use bid/ask, order-book depth, volatility-specific impact, financing and borrow constraints.
3. SPY and QQQ share substantial economic equity exposure. Equal weights do not mean equal risk contributions.
4. A risk model's exceedance backtest and an allocation strategy's investment performance are distinct evaluations.
5. No independent total-return adjustment reconciliation; no actual US Treasury yields, FX hedging, cash returns or historical point-in-time macro releases.
6. Because the reviewed period has already been examined, no result here supports claims of *new untouched out-of-sample alpha* or market beating.

## Further research before institutional-style claims

Secure licensed price/total-return history, perform vendor reconciliation, freeze a future truly untouched validation window, expand venue-specific instruments and liquidity assumptions, and add live paper-trading logs before discussing deployability.
'''
    (out / 'EMPIRICAL_RESEARCH_MEMO.md').write_text(report, encoding='utf-8')

    if include_plotly:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        fig = make_subplots(rows=2, cols=2,
            subplot_titles=('Growth of $1 (observed panel; modeled costs)',
                            'Drawdown from 2023 onwards', 'One-way cost sensitivity / CAGR (%)',
                            'Historical 99% VaR exceedances'),
            vertical_spacing=.16, horizontal_spacing=.12)
        for col in ['SPY_buy_hold_net','60_40','equal_3','inverse_vol_63']:
            wealth = (1+study.daily[col]).cumprod()
            fig.add_trace(go.Scatter(x=wealth.index,y=wealth,mode='lines',name=col),row=1,col=1)
            interval=study.daily.loc[TEST_START:,col]
            nav=(1+interval).cumprod()
            peak=np.maximum.accumulate(np.r_[1.,nav.to_numpy()])[1:]
            fig.add_trace(go.Scatter(x=nav.index,y=(nav.to_numpy()/peak-1)*100,
                                     mode='lines',name=f'{col} drawdown',showlegend=False),row=1,col=2)
        for s in ('60_40','equal_3','inverse_vol_63'):
            x=study.cost_sensitivity.query('strategy == @s and period == "reviewed_2023_2025"')
            fig.add_trace(go.Scatter(x=x.one_way_cost_bps,y=x.cagr_pct,
                      mode='lines+markers',name=f'{s} cost sensitivity',showlegend=False),row=2,col=1)
        f=study.risk_forecasts.query('strategy == "SPY_buy_hold_net"').copy()
        fig.add_trace(go.Scatter(x=f['Date'],y=f['loss']*100,mode='lines',
                name='SPY daily loss %',showlegend=False),row=2,col=2)
        fig.add_trace(go.Scatter(x=f['Date'],y=f['var_historical']*100,
                    mode='lines',name='SPY HS 99% VaR',showlegend=False),row=2,col=2)
        fig.update_layout(height=1050, width=1330, template='plotly_white',
            title=f'ATLAS | {classification} — Retrospective / Not Tradable',
            legend={'orientation':'h','y':1.08})
        fig.update_yaxes(title_text='NAV multiplier',row=1,col=1)
        fig.update_yaxes(title_text='Drawdown (%)',row=1,col=2)
        fig.update_yaxes(title_text='CAGR (%)',row=2,col=1)
        fig.update_yaxes(title_text='Daily loss / VaR (%)',row=2,col=2)
        fig.write_html(str(out/'research_dashboard.html'),include_plotlyjs=True,full_html=True)

    digest = {file.name: hashlib.sha256(file.read_bytes()).hexdigest()
              for file in out.iterdir() if file.is_file() and file.name != 'OUTPUT_SHA256.json'}
    (out / 'OUTPUT_SHA256.json').write_text(json.dumps(digest,indent=2,sort_keys=True),encoding='utf-8')
    return digest
