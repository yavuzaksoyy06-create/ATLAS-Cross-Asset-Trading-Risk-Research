"""ATLAS: pinned reproducible historical-data case study.

Historical ETF proxy data are downloaded from a *pinned* GitHub archive. This
module does not assert that archived vendor adjustments are independently audited.
An archive redistributing financial prices may have licensing restrictions;
raw CSV is intentionally never written to the shipped project results.

Run: python -m atlas.real_study --output results/real_market
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import urllib.request
from pathlib import Path

from .research_labels import source_kind, is_pinned

import numpy as np
import pandas as pd

ARCHIVE_REPO = 'revred/TradeSmart.Tracker'
ARCHIVE_COMMIT = '7d9d769b0f2ddcedf4c1703cc979b865a37b580d'
GIT_BLOBS = {
    'SPY': '38acc25a077e23fdf107102960c3df32f1543a7d',
    'QQQ': '410dc48d874ab666b6e22f529f395c0d9ca70060',
    'TLT': '24c628146c0d393589cc3aba3b290156a7703639',
}
SYMBOLS = ('SPY', 'QQQ', 'TLT')
FIRST_DATE = '2018-01-01'
LAST_DATE = '2025-12-31'
TEST_START = '2023-01-03'
REBALANCE_SESSIONS = 21
TRADING_COST_PER_ONE_WAY_TURNOVER = 0.0008  # 3 bp assumed fee + 5 bp assumed slippage


def blob_sha1(raw: bytes) -> str:
    """Git SHA1 of the raw byte-content, not a provider correctness guarantee."""
    header = b'blob ' + str(len(raw)).encode('ascii') + b'\x00'
    return hashlib.sha1(header + raw).hexdigest()


def archive_url(ticker: str) -> str:
    if ticker not in SYMBOLS:
        raise ValueError('Ticker not included in pinned study')
    return (f'https://raw.githubusercontent.com/{ARCHIVE_REPO}/'
            f'{ARCHIVE_COMMIT}/market/us/{ticker.lower()}.csv')


def parse_archive_csv(raw: bytes, ticker: str) -> pd.Series:
    """Parse archived adjusted-close *claim* and require a genuine price panel."""
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    if not {'Date', 'Close'}.issubset(set(reader.fieldnames or [])):
        raise ValueError('Data source does not provide the required Date,Close schema')
    records = []
    for row in reader:
        if FIRST_DATE <= row['Date'] <= LAST_DATE:
            records.append((row['Date'], float(row['Close'])))
    if not records:
        raise ValueError(f'No historical data for {ticker}')
    dates = pd.to_datetime([x[0] for x in records], errors='raise')
    prices = pd.Series([x[1] for x in records], index=dates, name=ticker, dtype=float)
    if not prices.index.is_monotonic_increasing or prices.index.has_duplicates:
        raise ValueError(f'Duplicate or unordered historical dates: {ticker}')
    if not np.isfinite(prices.to_numpy()).all() or (prices <= 0).any():
        raise ValueError(f'Invalid historical prices: {ticker}')
    return prices


def read_pinned_market_data(timeout: int = 25, archive_dir: str | Path | None = None) -> tuple[pd.DataFrame, dict]:
    """Load exact pinned source bytes from network or a local archive directory.

    Local source files are accepted only if every complete CSV's Git blob SHA1
    matches the constants for the pinned commit. This is NOT the unverified
    wide-format CSV mode. No local files are rewritten.
    """
    root = Path(archive_dir).expanduser().resolve() if archive_dir is not None else None
    if root is not None and not root.is_dir():
        raise FileNotFoundError(f'Pinned archive directory not found: {root}')
    cols = {}
    downloaded_sha256 = {}
    for ticker in SYMBOLS:
        if root is None:
            request = urllib.request.Request(archive_url(ticker), headers={
                'User-Agent': 'ATLAS-open-research/1.2 (historical data integrity study)',
                'Accept': 'text/csv',
            })
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read()
        else:
            # Explicitly fixed filenames; no user-supplied arbitrary path join.
            raw = (root / f'{ticker.lower()}.csv').read_bytes()
        observed_sha = blob_sha1(raw)
        if observed_sha != GIT_BLOBS[ticker]:
            raise ValueError(f'{ticker} downloaded bytes differ from expected pinned Git blob')
        downloaded_sha256[ticker] = hashlib.sha256(raw).hexdigest()
        cols[ticker] = parse_archive_csv(raw, ticker)
    prices = pd.concat(cols, axis=1, join='inner').sort_index()
    if prices.empty or prices.isna().any().any() or len(prices) < 800:
        raise ValueError('Too few common complete market sessions')
    if any(len(cols[s]) != len(prices) for s in SYMBOLS):
        raise ValueError('Archived price dates disagree between assets; refusing silent inner join')
    if str(prices.index[0].date()) != '2018-01-02' or str(prices.index[-1].date()) != '2025-12-31':
        raise ValueError('Archived time coverage changed or incomplete')
    # This sanity check protects against accidentally using future/illustrative bars.
    crash_day = prices.index.get_loc(pd.Timestamp('2020-03-16'))
    observed_spy_drop = prices['SPY'].iloc[crash_day] / prices['SPY'].iloc[crash_day-1] - 1
    if not (-.112 < observed_spy_drop < -.107):
        raise ValueError('Expected historical March 16, 2020 SPY observation missing')
    metadata = {
        'data_category': 'HISTORICAL_ARCHIVED_ETF_CLOSES_NOT_SYNTHETIC',
        'origin_archive': f'https://github.com/{ARCHIVE_REPO}',
        'origin_description': 'Archive README names Stooq primary / Yahoo secondary. Not independently audited.',
        'pinned_repository_commit': ARCHIVE_COMMIT,
        'git_blob_sha1': GIT_BLOBS,
        'raw_file_sha256': downloaded_sha256,
        'source_urls': {ticker: archive_url(ticker) for ticker in SYMBOLS},
        'source_acquisition': 'local Git-blob-verified CSV copies' if root is not None else 'HTTPS pinned archive download',
        'first_observation': str(prices.index[0].date()),
        'last_observation': str(prices.index[-1].date()),
        'observations': len(prices),
        'price_adjustment': 'Archive says close adjusted for dividends and splits; third-party claim unverified.',
        'redistribution': 'No raw third-party historical market files included; check usage rights.',
    }
    return prices, metadata


def make_targets(history: np.ndarray, strategy: str) -> np.ndarray:
    """history rows contain only returns observed before the current session."""
    if strategy == '60_40':
        return np.array([.60, 0.0, .40])
    if strategy == 'equal_3':
        return np.array([1/3, 1/3, 1/3])
    if strategy == 'inverse_vol_63':
        recent = history[-63:]
        with np.errstate(invalid='ignore', divide='ignore'):
            # Mirrors population-undefined first-observation handling in reference JS.
            v = np.std(recent, axis=0, ddof=1) if len(recent) > 1 else np.zeros(3)
            inv = 1 / np.maximum(v, 1e-6)
        return inv / inv.sum()
    raise ValueError('Unsupported strategy')


def historical_backtest(prices: pd.DataFrame, strategy: str, cost: float = TRADING_COST_PER_ONE_WAY_TURNOVER,
                        rebalance: int = REBALANCE_SESSIONS) -> pd.Series:
    """Fully invested, funded long-only strategy with weight drift and assumed costs.

    Day i uses returns up through i-1 for weights before incurring day i return;
    close-to-close trades at prior close are only an approximation to executable fills.
    """
    if list(prices.columns) != list(SYMBOLS):
        raise ValueError(f'Expected columns {SYMBOLS}')
    if not 0 <= cost < 1 or rebalance < 1 or len(prices) < 65:
        raise ValueError('Bad cost, rebalance frequency or observation count')
    r = prices.pct_change(fill_method=None).fillna(0).to_numpy()
    weights = np.zeros(3)
    daily = np.zeros(len(prices))
    for i in range(1, len(prices)):
        trade_cost = 0.0
        if i == 1 or (i - 1) % rebalance == 0:
            desired = make_targets(r[max(1, i-63):i], strategy)
            trade_cost = float(np.abs(desired - weights).sum()) * cost
            weights = desired
        gross = float(np.dot(weights, r[i]))
        daily[i] = gross - trade_cost
        weights = weights * (1 + r[i]) / (1 + gross)
    return pd.Series(daily[1:], index=prices.index[1:], name=strategy)


def strategy_summary(series: pd.Series) -> dict:
    x = series.to_numpy(float)
    n = len(x)
    if n < 30 or not np.isfinite(x).all() or np.any(x <= -1):
        raise ValueError('Invalid or too-short strategy return history')
    wealth = np.cumprod(1+x)
    # The reference evaluator initializes peak at 1 (the investable initial NAV).
    peak = np.maximum.accumulate(np.concatenate(([1.], wealth)))[1:]
    dd = wealth/peak - 1
    std = float(np.std(x, ddof=1))
    tail = np.sort(x)
    tail_count = max(1, math.ceil(n*.05))
    return {
        'sessions': n,
        'cumulative_return_pct': float((wealth[-1]-1)*100),
        'annualized_return_pct': float((wealth[-1]**(252/n)-1)*100),
        'annualized_volatility_pct': float(std*np.sqrt(252)*100),
        'sharpe_zero_risk_free_rate': float(np.mean(x)/std*np.sqrt(252)) if std else None,
        'max_drawdown_pct': float(np.min(dd)*100),
        'historical_var_95_daily_loss_pct': float(-tail[int(np.floor(n*.05))]*100),
        'historical_es_95_daily_loss_pct': float(-np.mean(tail[:tail_count])*100),
    }


def run_study(prices: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    full_returns = prices['SPY'].pct_change(fill_method=None).iloc[1:].rename('SPY_benchmark_no_cost')
    for strategy in ('60_40', 'equal_3', 'inverse_vol_63'):
        full_returns = pd.concat((full_returns, historical_backtest(prices, strategy)), axis=1)
    if full_returns.isna().any().any():
        raise ValueError('Missing daily outputs')
    summary = {label: {
        '2018_2025': strategy_summary(full_returns[label]),
        '2023_2025_chronological_segment': strategy_summary(full_returns.loc[TEST_START:, label]),
    } for label in full_returns.columns}
    return full_returns, summary


def write_study(output: Path, full_returns: pd.DataFrame, summary: dict, source: dict):
    output.mkdir(parents=True, exist_ok=True)
    metadata = {
        'dataset': source,
        'research_parameters': {
            'dates': [str(full_returns.index.min().date()), str(full_returns.index.max().date())],
            'chronological_segment_start': TEST_START,
            'source_classification': source_kind(source),
            'trading_days_per_year': 252,
            'strategies': ['SPY_benchmark_no_cost', '60_40', 'equal_3', 'inverse_vol_63'],
            'rebalance_every_sessions': REBALANCE_SESSIONS,
            'portfolio_fee_bps': 3, 'portfolio_slippage_bps': 5,
            'benchmark_costs': 'SPY uncosted price-change benchmark',
            'risk_free_rate': '0% assumption; not excess-of-cash Sharpe',
            'strategy_tuning': 'Rules fixed; no predictive ML training or grid search.',
            'data_split_integrity': ('Retrospective chronological segment, NOT a pristine never-inspected '
                                     'holdout: its outcomes are already reviewed.'),
        },
        'performance': summary,
        'limitations': [
            f'Source class: {source_kind(source)}. Upstream adjustment, sampling and rights not independently validated.',
            'Risk is historical and does not predict future loss.',
            'Indicative fee/slippage assumptions: no spread/ADV/time-of-day measurements.',
            'Sample survivorship and asset selection may bias conclusions.',
            'This legacy SPY reference has no modeled trading fees, whereas the portfolio rules do; institutional comparator adds the costed benchmark.',
            f'Data ends {full_returns.index.max().date()}; this is not live pricing.',
        ],
    }
    (output/'result.json').write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding='utf-8')
    full_returns.to_csv(output/'derived_daily_returns.csv', index_label='Date')
    pinned = is_pinned(source)
    actual_first = str(full_returns.index.min().date())
    actual_last = str(full_returns.index.max().date())
    label = source_kind(source)
    title = ('ATLAS — Historical ETF Proxy Study (2018–2025)' if pinned else
             'ATLAS — Input-Panel Engineering Audit (not verified market evidence)')
    rows = [
        f'# {title}', '',
        f'> **SOURCE CLASS: {label}**', '',
        'The archive asserts adjusted closes but its corporate-action adjustments and data rights are not independently audited.'
        if pinned else 'This report is generated from an externally supplied or synthetic input panel; it is NOT verified archived market performance.',
        '', '## Evaluation settings',
        f'- Actual daily-return index: {actual_first} through {actual_last}; {len(full_returns):,} return sessions.',
        '- 2023+ period, if included, was previously reviewed and is NOT an untouched holdout.',
        '- Strategies: SPY reference (no costs), fixed 60% SPY/40% TLT, equal-third, inverse 63-session volatility.',
        '- Portfolio rebalances every 21 sessions; assumed one-way turnover cost: 8 bps.',
        '- Daily closes are not executable quotes; fee and slippage assumptions are simplified.',
        '', '## Results — reviewed observations from 2023 onward', '',
        '| Strategy | CAGR | Annual volatility | Sharpe (0% rf) | Max drawdown | VaR (daily 95%) |',
        '|---|---:|---:|---:|---:|---:|',
    ]
    for key, values in summary.items():
        s = values['2023_2025_chronological_segment']
        rows.append(f"| {key} | {s['annualized_return_pct']:.2f}% | "
                    f"{s['annualized_volatility_pct']:.2f}% | "
                    f"{s['sharpe_zero_risk_free_rate']:.2f} | "
                    f"{s['max_drawdown_pct']:.2f}% | "
                    f"{s['historical_var_95_daily_loss_pct']:.2f}% |")
    rows.extend(['', '## Interpretation',
                 'Numbers describe the specified panel and assumptions only. Portfolio diversification trades upside for downside protection in some periods; it does not prove alpha.',
                 '', '## Verification / rights',
                 f"Source: {source.get('origin_archive','unspecified')}",
                 f'Data label: {label}',
                 ('The pinned download checks Git blobs and records raw SHA256 hashes. Redistribution rights and total-return accuracy are not independently audited.'
                  if pinned else 'No pinned archive or independent vendor provenance checks were performed on this input.'),
                 '', '## Methodological limitations',
                 'Potential asset selection and survivorship bias, close-to-close rather than executable fills, constant costs, assumed 0% risk-free rate, post-hoc period inspection and no pristine out-of-sample validation.', ''])
    (output/'CASE_STUDY.md').write_text('\n'.join(rows), encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser(description='Reproduce archived real ETF study')
    parser.add_argument('--output', default='results/real_market')
    parser.add_argument('--input-csv', default=None,
        help='Optional LOCAL wide-format adjusted-price CSV (Date,SPY,QQQ,TLT). NOT pinned/verified.')
    parser.add_argument('--archive-dir', default=None,
        help='Directory containing pinned spy.csv, qqq.csv, tlt.csv; complete Git blob SHA1 verification required.')
    parser.add_argument('--repetitions', type=int, default=500,
        help='Paired block-bootstrap repetitions (>=100)')
    parser.add_argument('--synthetic-fixture', action='store_true',
        help='Explicitly label a supplied CSV as synthetic engineering data (requires --input-csv)')
    parser.add_argument('--classic-only', action='store_true',
        help='Skip institutional risk audit; run earlier v0.3 summaries only')
    args = parser.parse_args()
    if args.archive_dir and args.input_csv:
        parser.error('--archive-dir and --input-csv are mutually exclusive')
    if args.synthetic_fixture and args.archive_dir:
        parser.error('--synthetic-fixture cannot be used with --archive-dir; pinned bytes have a fixed identity')
    if args.synthetic_fixture and not args.input_csv:
        parser.error('--synthetic-fixture requires --input-csv')
    if args.input_csv:
        from .data import load_csv
        prices = load_csv(args.input_csv)
        if list(prices.columns) != list(SYMBOLS):
            parser.error('Local CSV must have Date,SPY,QQQ,TLT, in that order')
        meta = {
            'data_category': ('SYNTHETIC_TEST_FIXTURE' if args.synthetic_fixture
                              else 'USER_SUPPLIED_UNVERIFIED_ADJUSTED_PRICE_CLAIM'),
            'origin_archive': str(args.input_csv),
            'source_urls': {},
            'price_adjustment': ('Computer-generated synthetic levels; not market prices'
                                 if args.synthetic_fixture else 'User declaration only. Not independently verified.'),
            'redistribution': 'User must verify data rights.',
            'last_observation': str(prices.index[-1].date()),
        }
    else:
        prices, meta = read_pinned_market_data(archive_dir=args.archive_dir)
    daily, summary = run_study(prices)
    out = Path(args.output)
    write_study(out, daily, summary, meta)
    if not args.input_csv:
        from .reference_validation import check_reference
        reference = Path(__file__).resolve().parents[2] / 'research/real_market_2018_2025/REFERENCE_RESULTS.json'
        if not reference.is_file():
            # Source-only packages may not bundle research reference; don't conceal it.
            raise FileNotFoundError('Pinned archive reconciliation file is missing: ' + str(reference))
        checked = check_reference(summary, meta, reference)
        (out / 'reference_reconciliation.json').write_text(json.dumps(checked, indent=2), encoding='utf-8')
        print('Pinned archive reference reconciliation:', checked['status'])
    print(f'Price observations: {len(prices)}, {prices.index.min().date()}–{prices.index.max().date()}')
    print(f"SPY post-2023 segment CAGR (NO COST): {summary['SPY_benchmark_no_cost']['2023_2025_chronological_segment']['annualized_return_pct']:.2f}%")
    if not args.classic_only:
        from .institutional_report import investigate, publish
        full = investigate(prices, bootstrap_repetitions=args.repetitions)
        publish(full, out / 'institutional', meta)
        print('Published independent costed SPY comparator, event windows, 99% VaR coverage and uncertainty.')
    print('SOURCE CATEGORY:', source_kind(meta))
    print('RESEARCH LIMIT: Reviewed 2023–25 segment is NOT an untouched independent holdout.')
    print('Outputs:',out)

if __name__ == '__main__':
    main()
