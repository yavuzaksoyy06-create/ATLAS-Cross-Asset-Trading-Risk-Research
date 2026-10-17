"""Named historical stress windows with ex-post selection disclosed.

Unlike hypothetical one-step shocks, these are replay of realized strategy
returns. Windows selected after the facts; no predictive interpretation.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

# Close-to-close returns INCLUDED if the observation date falls within window.
EVENTS = {
    'COVID liquidity shock': ('2020-02-19','2020-03-23'),
    'Inflation and duration repricing': ('2022-01-03','2022-10-14'),
    'US regional banking stress': ('2023-03-08','2023-03-24'),
    '2024 summer growth repricing': ('2024-07-16','2024-08-05'),
}


def replay_event_windows(daily_returns: pd.DataFrame,
                         events: dict[str, tuple[str,str]] | None = None) -> pd.DataFrame:
    if (not isinstance(daily_returns.index,pd.DatetimeIndex) or daily_returns.index.has_duplicates
        or not daily_returns.index.is_monotonic_increasing or daily_returns.empty
        or daily_returns.isna().any().any() or not np.isfinite(daily_returns.to_numpy()).all()
        or (daily_returns<=-1).any().any()):
        raise ValueError('Need finite, clean and sorted date-indexed return panel')
    records=[]
    for label,(start,end) in (events or EVENTS).items():
        if pd.Timestamp(end)<pd.Timestamp(start):
            raise ValueError('Invalid event window')
        window=daily_returns.loc[start:end]
        if len(window)<3:
            continue
        for asset in window:
            r=window[asset].to_numpy()
            wealth=np.cumprod(1+r)
            peak=np.maximum.accumulate(np.concatenate(([1.],wealth)))[1:]
            records.append({'event':label,'asset_or_strategy':asset,
                'requested_start':start,'requested_end':end,
                'first_session':str(window.index[0].date()),
                'last_session':str(window.index[-1].date()),'sessions':len(window),
                'cumulative_return':float(wealth[-1]-1),
                'worst_peak_to_trough':float((wealth/peak-1).min()),
                'worst_session':float(r.min())})
    return pd.DataFrame.from_records(records)
