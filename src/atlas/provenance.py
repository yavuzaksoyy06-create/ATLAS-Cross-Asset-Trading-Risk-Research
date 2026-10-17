"""Deterministic research snapshots and transparent data-lineage manifests.

This is a dataset integrity layer, not evidence of licensing, clean corporate
acts, vendor point-in-time validity, or an accurate tradeable total return.
"""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import pandas as pd
from .data import validate_prices


def snapshot_prices(prices: pd.DataFrame, source: str, output: str | Path,
                    adjustment: str = "source_declared_adjusted_close") -> dict:
    """Save exactly what was analysed and SHA256-hash the on-disk bytes."""
    panel = validate_prices(prices)
    target = Path(output)
    target.mkdir(parents=True, exist_ok=True)
    path = target / "adjusted_prices_snapshot.csv"
    panel.to_csv(path, index_label="Date", float_format="%.17g")
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    first, last = panel.index[0], panel.index[-1]
    # Weekdays missing includes official market holidays: diagnostic, NOT errors.
    weekdays = pd.bdate_range(first, last)
    missing_weekdays = len(weekdays.difference(panel.index.normalize()))
    manifest = {
        "format_version": 1,
        "source": source,
        "data_label": "SYNTHETIC - NOT MARKET DATA" if "SYNTHETIC" in source.upper() else "SOURCE-DECLARED RESEARCH PRICES",
        "adjustment_claim": adjustment,
        "snapshot_file": path.name,
        "original_index_name": panel.index.name,
        "sha256": sha,
        "saved_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "row_count": len(panel),
        "column_count": panel.shape[1],
        "columns": list(panel.columns),
        "first_date": first.strftime("%Y-%m-%d"),
        "last_date": last.strftime("%Y-%m-%d"),
        "missing_weekdays_including_exchange_holidays": missing_weekdays,
        "nonincreasing_observations_by_asset": {
            col: int((panel[col].diff().iloc[1:] <= 0).sum()) for col in panel.columns
        },
        "rights_warning": "Check vendor terms before committing raw data to public repositories.",
        "survivorship_warning": "Current ETF universe is selected with hindsight; not survivorship-free.",
    }
    (target / "data_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def verify_snapshot(output: str | Path) -> tuple[pd.DataFrame, dict]:
    """Re-read raw bytes and enforce the original manifest/column/date metadata."""
    target = Path(output)
    manifest = json.loads((target / "data_manifest.json").read_text(encoding="utf-8"))
    name = manifest.get("snapshot_file")
    if name != "adjusted_prices_snapshot.csv":
        raise ValueError("Unexpected snapshot filename: refusing arbitrary path.")
    path = target / name
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest["sha256"]:
        raise ValueError("Snapshot SHA256 mismatch: data modified after freezing.")
    panel = pd.read_csv(path, parse_dates=["Date"]).set_index("Date")
    panel = validate_prices(panel)
    panel.index.name = manifest.get("original_index_name")
    if (len(panel) != manifest["row_count"] or list(panel.columns) != manifest["columns"]
            or panel.index[0].strftime("%Y-%m-%d") != manifest["first_date"]
            or panel.index[-1].strftime("%Y-%m-%d") != manifest["last_date"]):
        raise ValueError("Snapshot metadata and contents disagree.")
    return panel, manifest
