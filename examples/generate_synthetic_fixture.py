"""Offline sample CSV generator; NEVER use its returns as historical evidence."""
from pathlib import Path
import numpy as np
import pandas as pd


def main() -> None:
    out = Path(__file__).resolve().parent / 'synthetic_3etf.csv'
    rng = np.random.default_rng(20261017)
    dates = pd.bdate_range('2020-01-01', periods=925)
    r = rng.normal(loc=[.0003,.00035,.0001],scale=[.009,.012,.007],size=(len(dates),3))
    p = 100 * np.exp(np.cumsum(r,axis=0))
    df = pd.DataFrame(p, columns=['SPY','QQQ','TLT'])
    df.insert(0,'Date',dates.strftime('%Y-%m-%d'))
    df.to_csv(out,index=False,float_format='%.8f')
    print('SYNTHETIC DEMO ONLY:',out)


if __name__ == '__main__':
    main()
