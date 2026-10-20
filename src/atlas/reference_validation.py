"""Numerical reconciliation against the independently recorded archived-price study.

The reference results were computed earlier using a separate JavaScript evaluator
on GitHub-retrieved prices, *not* a synthetic fixture. This check runs only after
actual pinned archive download. It does not independently validate source quality.
"""
from __future__ import annotations
import json
from pathlib import Path
import math
from .real_study import ARCHIVE_COMMIT, GIT_BLOBS, SYMBOLS


METRICS = ('cumulative_return_pct', 'annualized_return_pct',
           'annualized_volatility_pct', 'max_drawdown_pct',
           'historical_var_95_daily_loss_pct', 'historical_es_95_daily_loss_pct')


def check_reference(summary: dict, source: dict, reference_path: str | Path,
                    tolerance_percentage_points: float = 0.05) -> dict:
    """Fail closed if real-data replication diverges from independent historical snapshot."""
    if (not math.isfinite(tolerance_percentage_points)
            or tolerance_percentage_points <= 0 or tolerance_percentage_points > 0.5):
        raise ValueError('Comparison tolerance must be in (0, 0.5] percentage points')
    if source.get('data_category') != 'HISTORICAL_ARCHIVED_ETF_CLOSES_NOT_SYNTHETIC':
        raise ValueError('Independent historical comparison requires the verified pinned downloader')
    if source.get('pinned_repository_commit') != ARCHIVE_COMMIT:
        raise ValueError('Archive commit mismatch')
    if source.get('git_blob_sha1') != GIT_BLOBS:
        raise ValueError('Downloaded blobs were not pinned to expected file versions')
    if source.get('observations') != 2011:
        raise ValueError('Unexpected historical dataset size')
    reference = json.loads(Path(reference_path).read_text(encoding='utf-8'))
    if (reference.get('git_commit') != ARCHIVE_COMMIT
        or reference.get('git_blobs') != GIT_BLOBS
        or reference.get('common_price_observations') != 2011
        or reference.get('prices_are_synthetic') is not False
        or reference.get('universe') != list(SYMBOLS)):
        raise ValueError('Historical reference metadata mismatch')
    differences = {}
    for strategy, periods in reference['results'].items():
        if strategy not in summary:
            raise ValueError(f'Missing strategy: {strategy}')
        for period in ('2018_2025', '2023_2025_chronological_segment'):
            if summary[strategy][period]['sessions'] != periods[period]['sessions']:
                raise ValueError(f'Session mismatch {strategy}/{period}')
            for key in METRICS:
                computed = float(summary[strategy][period][key]); expected = float(periods[period][key])
                if (not math.isfinite(computed) or not math.isfinite(expected)
                        or abs(computed - expected) > tolerance_percentage_points):
                    raise ValueError(f'Reference discrepancy {strategy}/{period}/{key}: {computed} vs {expected}')
                differences[f'{strategy}/{period}/{key}'] = round(computed - expected, 8)
    return {'status':'PASSED_REFERENCE_NUMERICAL_RECONCILIATION',
            'reference_kind':'Independent JavaScript evaluator of pinned archived public ETF closes',
            'tested_metrics':len(differences),
            'tolerance_percentage_points':tolerance_percentage_points,
            'max_absolute_difference_percentage_points':max(abs(x) for x in differences.values()),
            'limits':'Checks numerical agreement only; does not certify vendor dividends, prices, data rights or alpha.'}
