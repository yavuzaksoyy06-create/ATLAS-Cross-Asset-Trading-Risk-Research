"""Market-data ingestion with explicit synthetic/real provenance."""
from __future__ import annotations
import numpy as np
import pandas as pd

TICKERS = ["SPY", "QQQ", "IWM", "EEM", "TLT", "IEF", "GLD", "UUP", "HYG", "BIL"]


def validate_prices(prices: pd.DataFrame, *, minimum_assets: int = 2) -> pd.DataFrame:
    """Normalize and validate wide adjusted-close price matrices.

    Missing rows are intentionally NOT forward-filled: that can hide stale prices.
    """
    if not isinstance(prices.index, pd.DatetimeIndex):
        raise ValueError("Index must be a DatetimeIndex.")
    if not isinstance(minimum_assets, int) or minimum_assets < 1:
        raise ValueError("minimum_assets must be a positive integer.")
    if prices.empty or prices.shape[1] < minimum_assets:
        raise ValueError(f"At least {minimum_assets} assets and one observation are required.")
    if prices.index.has_duplicates or not prices.index.is_monotonic_increasing:
        raise ValueError("Dates must be unique and sorted ascending.")
    if prices.columns.duplicated().any():
        raise ValueError("Duplicate tickers are not permitted.")
    prices = prices.copy().astype(float)
    if prices.isna().any().any() or not np.isfinite(prices.to_numpy()).all():
        raise ValueError("Missing/infinite prices detected: clean or reject explicitly.")
    if (prices <= 0).any().any():
        raise ValueError("All adjusted close prices must be positive.")
    return prices


def synthetic_prices(n_days: int = 1700, seed: int = 2026) -> pd.DataFrame:
    """Reproducible correlated demo data, NEVER real/historical market observations."""
    if n_days < 300:
        raise ValueError("At least 300 synthetic days required for rolling analysis.")
    rng = np.random.default_rng(seed)
    factors = rng.standard_normal((n_days, 5))
    regime = np.ones(n_days)
    regime[int(n_days * .35):int(n_days * .44)] = 2.7
    regime[int(n_days * .74):int(n_days * .80)] = 1.9
    equity, rates, dollar, credit, metal = factors.T
    e = equity * regime
    r = rates * (0.6 + 0.35 * regime)
    c = credit * regime
    noise = rng.normal(0, .0005, (n_days, len(TICKERS)))
    # Coefficients in fractions per trading day. Qualitative factor structure only.
    exposures = np.column_stack([
        .00035 + .0085*e - .0015*r + .0010*c,
        .00045 + .0115*e - .0025*r + .0015*c,
        .0003 + .0110*e - .0020*r + .0020*c,
        .00030 + .0098*e - .0014*r - .0020*dollar + .0020*c,
        .0001 - .0012*e + .0100*r,
        .00012 - .0005*e + .0037*r,
        .0002 - .0020*e - .0012*r - .0025*dollar + .0070*metal,
        .0001 - .0010*e + .0060*dollar,
        .00022 + .0038*e - .0020*r + .0032*c,
        .00010 + .00012*r,
    ])
    returns = np.maximum(exposures + noise, -0.8)
    px = 100.0 * np.cumprod(1.0 + returns, axis=0)
    idx = pd.bdate_range(end="2026-10-16", periods=n_days)
    return validate_prices(pd.DataFrame(px, index=idx, columns=TICKERS))


def load_csv(path: str) -> pd.DataFrame:
    """CSV columns: Date, SPY, ... containing ADJUSTED close prices."""
    df = pd.read_csv(path)
    if "Date" not in df:
        raise ValueError("CSV must include a 'Date' column.")
    df["Date"] = pd.to_datetime(df["Date"], errors="raise", utc=True).dt.tz_localize(None)
    df = df.set_index("Date")
    return validate_prices(df)


def yahoo_prices(tickers: list[str], start: str = "2015-01-01", end: str | None = None) -> pd.DataFrame:
    """Optional third-party public research feed; verify terms and adjustments.

    We use auto-adjusted close so that splits/dividends do not create mechanical
    jumps. This is NOT point-in-time survivorship-free institutional data.
    """
    try:
        import yfinance as yf
    except ImportError as exc:
        raise ImportError("Install with: pip install -e '.[markets]'") from exc
    raw = yf.download(tickers, start=start, end=end, auto_adjust=True,
                      progress=False, group_by="column", threads=False)
    if raw.empty:
        raise ValueError("Feed returned no prices; verify symbols and dates.")
    close = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw[["Close"]]
    if not isinstance(raw.columns, pd.MultiIndex):
        close.columns = [tickers[0]]
    close = close.reindex(columns=tickers).dropna(how="any")
    if close.empty:
        raise ValueError("No common dates with valid prices across selected assets.")
    close.index = pd.to_datetime(close.index, utc=True).tz_localize(None)
    return validate_prices(close)


def price_returns(prices: pd.DataFrame) -> pd.DataFrame:
    return validate_prices(prices).pct_change(fill_method=None).iloc[1:]
