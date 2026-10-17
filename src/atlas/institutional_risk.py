"""Ex-ante market risk: historical simulation, parametric EWMA and exception diagnostics.

Strictly one-step-ahead: prediction indexed t is computed from sessions < t.
Research only; risk model assumptions are not regulatory capital estimates.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy.stats import chi2, norm


def _loglik_bernoulli(successes: int, trials: int) -> float:
    if trials == 0:
        return 0.0
    p = successes / trials
    if successes == 0:
        return trials * float(np.log1p(-p))
    if successes == trials:
        return trials * float(np.log(p))
    return successes * float(np.log(p)) + (trials - successes) * float(np.log1p(-p))


def exception_tests(exceptions: pd.Series | np.ndarray, confidence: float = .99) -> dict:
    """Kupiec LRuc and Christoffersen independence LRind (asymptotic chi-squared).

    Small sample / rare-event p-values can be misleading; report counts too.
    """
    x = np.asarray(exceptions, dtype=int)
    if len(x) < 30 or np.any((x != 0) & (x != 1)) or not 0 < confidence < 1:
        raise ValueError('30+ binary exceptions and valid confidence required')
    n, k = len(x), int(x.sum())
    p0 = 1 - confidence
    ll_null = k * np.log(p0) + (n - k) * np.log1p(-p0)
    ll_mle = _loglik_bernoulli(k, n)
    lr_uc = max(0., 2. * (ll_mle - ll_null))
    a = x[:-1]; b = x[1:]
    n00 = int(((a == 0) & (b == 0)).sum())
    n01 = int(((a == 0) & (b == 1)).sum())
    n10 = int(((a == 1) & (b == 0)).sum())
    n11 = int(((a == 1) & (b == 1)).sum())
    l_unrestricted = _loglik_bernoulli(n01, n00+n01) + _loglik_bernoulli(n11, n10+n11)
    l_restricted = _loglik_bernoulli(n01+n11, n00+n01+n10+n11)
    lr_ind = max(0., 2. * (l_unrestricted - l_restricted))
    return {
        'observations': n, 'breaches': k, 'breach_rate': k / n,
        'expected_breaches': n * p0, 'target_breach_rate': p0,
        'kupiec_lr_uc': lr_uc, 'kupiec_pvalue': float(chi2.sf(lr_uc, 1)),
        'christoffersen_lr_ind': lr_ind, 'christoffersen_independence_pvalue': float(chi2.sf(lr_ind, 1)),
        'christoffersen_lr_cc': lr_uc + lr_ind,
        'christoffersen_coverage_pvalue': float(chi2.sf(lr_uc + lr_ind, 2)),
        'transitions': {'n00':n00,'n01':n01,'n10':n10,'n11':n11},
        'warning': 'Asymptotic test; low exception counts compromise power, not regulatory validation.',
    }


def ewma_forecast_variance(history: np.ndarray, decay: float = .94) -> float:
    """EWMA conditional variance at next session using past demeaned returns only."""
    y = np.asarray(history, dtype=float)
    if y.ndim != 1 or len(y) < 30 or not np.isfinite(y).all() or not 0 < decay < 1:
        raise ValueError('Require 30+ finite historical returns and decay in (0,1)')
    # Initial unbiased sample estimate; subsequent filter uses only observed old returns.
    v = float(np.var(y[:min(30, len(y))], ddof=1))
    for value in y[min(30, len(y)):]:
        v = decay*v + (1-decay)*float(value**2)
    return v


@dataclass
class RiskBacktest:
    forecasts: pd.DataFrame
    diagnostics: pd.DataFrame
    settings: dict


def rolling_risk_validation(daily: pd.Series, window: int = 252,
                            confidence: float = .99, decay: float = .94) -> RiskBacktest:
    """Compare past-only historical VaR to Gaussian zero-mean EWMA VaR.

    Historical VaR uses empirical (loss) quantile at each t. EWMA assumes Gaussian
    conditional returns with no drift; this is a *model choice* not a universal truth.
    """
    x = pd.Series(daily, dtype=float)
    if (not isinstance(x.index, pd.DatetimeIndex) or x.index.has_duplicates
        or not x.index.is_monotonic_increasing or x.isna().any()
        or not np.isfinite(x.to_numpy()).all() or (x <= -1).any()
        or window < 60 or len(x) < window + 40 or not .5 < confidence < 1):
        raise ValueError('Use unique date sorted, finite daily returns, 60+ training, 40+ test rows')
    rows=[]
    z=float(norm.ppf(confidence))
    for i in range(window,len(x)):
        past=x.iloc[i-window:i].to_numpy()
        loss=float(-x.iloc[i]); hs=float(max(0., np.quantile(-past, confidence)))
        ew=float(max(0., z*np.sqrt(ewma_forecast_variance(past,decay))))
        rows.append((x.index[i], float(x.iloc[i]), loss, hs, ew, int(loss>hs), int(loss>ew)))
    frame=pd.DataFrame(rows,columns=['Date','return','loss','var_historical',
        'var_ewma_gaussian','breach_historical','breach_ewma']).set_index('Date')
    tests=[]
    for label,key in [('Historical simulation','breach_historical'),('Gaussian EWMA','breach_ewma')]:
        summary=exception_tests(frame[key],confidence)
        summary['model']=label
        summary['mean_predicted_var']=float(frame['var_historical' if key=='breach_historical' else 'var_ewma_gaussian'].mean())
        tests.append(summary)
    diag=pd.DataFrame(tests).set_index('model')
    settings={'window':window,'confidence':confidence,'ewma_decay':decay,
       'zero_mean_gaussian_ewma':True,'timing':'VaR forecast on t uses only observations before t',
       'limitations':'Daily closes, overlapping rolling estimators, thin tails, no intraday liquidity risks.'}
    return RiskBacktest(frame,diag,settings)
