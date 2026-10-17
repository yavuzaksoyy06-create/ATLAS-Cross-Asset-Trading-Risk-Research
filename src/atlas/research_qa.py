"""Publication-focused, deterministic research integrity checks."""
from __future__ import annotations
import numpy as np
import pandas as pd


def audit_prices(prices: pd.DataFrame, extreme_daily_change: float=.35)->dict:
    if not isinstance(prices.index,pd.DatetimeIndex) or prices.index.has_duplicates or not prices.index.is_monotonic_increasing:
        raise ValueError('Prices require unique, sorted date index')
    if prices.empty or prices.columns.duplicated().any():
        raise ValueError('Empty data or duplicate names')
    p=prices.astype(float)
    if p.isna().any().any() or not np.isfinite(p.to_numpy()).all() or (p<=0).any().any():
        raise ValueError('Nonpositive/missing/invalid prices')
    r=p.pct_change(fill_method=None).iloc[1:]
    flagged=[]
    for t in r:
        for dt,v in r.index[np.abs(r[t])>extreme_daily_change].to_series().items():
            flagged.append({'symbol':t,'date':str(dt.date()),'return':float(r.loc[dt,t])})
    gaps=p.index.to_series().diff().dropna().dt.days
    return {'first':str(p.index[0].date()),'last':str(p.index[-1].date()),
            'observations':len(p),'assets':list(p.columns),
            'duplicate_dates':int(p.index.duplicated().sum()),
            'week_gap_gt_5_calendar_days':int((gaps>5).sum()),
            'extreme_daily_moves':flagged,
            'warning':'Flags are triage, not proof of data errors. Splits, total-return and calendar assumptions must be checked against vendor records.'}


def cost_sensitivity(returns: pd.DataFrame, simulator,
                     costs_bps:tuple[int,...]=(0,2,8,15,30)) -> pd.DataFrame:
    """Caller supplies simulator(cost_bps)->daily returns; no optimization on results."""
    records=[]
    for cost in costs_bps:
        if cost<0: raise ValueError('No negative costs')
        s=simulator(float(cost)/10000)
        if len(s)!=len(returns) or s.isna().any():
            raise ValueError('Simulator must return complete aligned returns')
        wealth=float(np.prod(1+s.to_numpy()))
        records.append({'roundtrip_assumption_note':'Cost is per unit of one-way absolute turnover',
                        'one_way_bps':cost,'sessions':len(s),
                        'cumulative_return':wealth-1,
                        'annualized_return':wealth**(252/len(s))-1})
    return pd.DataFrame(records)
