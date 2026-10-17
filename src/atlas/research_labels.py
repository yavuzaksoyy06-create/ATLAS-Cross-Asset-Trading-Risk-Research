"""Strong dataset labels that prevent demo outputs from masquerading as market evidence."""
from __future__ import annotations


def source_kind(provenance: dict) -> str:
    """Source class only; no origin/archive metadata alone can verify a provider."""
    declared = str(provenance.get('data_category', '')).upper()
    desc = str(provenance.get('origin_archive', '')).upper()
    if declared == 'HISTORICAL_ARCHIVED_ETF_CLOSES_NOT_SYNTHETIC':
        # Assigned by the pinned downloader after byte/shape/time-range checks.
        return 'PINNED THIRD-PARTY ARCHIVE — UNVERIFIED PRICE ADJUSTMENT'
    if 'SYNTHETIC' in declared or 'SYNTHETIC' in desc:
        return 'SYNTHETIC ENGINEERING FIXTURE — NOT MARKET OBSERVATIONS'
    return 'UNVERIFIED USER-SUPPLIED PRICE PANEL — PROVENANCE UNCONFIRMED'


def is_pinned(provenance: dict) -> bool:
    return source_kind(provenance).startswith('PINNED')
