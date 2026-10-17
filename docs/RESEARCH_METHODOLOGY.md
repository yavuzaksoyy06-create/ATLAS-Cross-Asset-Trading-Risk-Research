# Quantitative research methodology

## Research question

When unlevered, long-only allocations between US equity and duration ETFs change, how do realized return distributions, downside tail risk and drawdowns change after modeled turnover costs? Do conventional volatility-based allocation rules produce robust improvements versus simple passive equity exposure?

## Fixed instruments and strategies

**Instrument universe:** SPY, QQQ, TLT. This set is an intentionally small set of *proxy ETFs*. It does not approximate all bonds, derivatives, currencies or credit instruments. SPY and QQQ share overlapping risk factors; the equal-weight rule is not an equal-risk construction.

**Rules:** `60_40` = 60% SPY / 40% TLT; `equal_3` = one-third each; `inverse_vol_63` = normalized inverse of trailing 63-session sample standard deviations, floored at 1e-6 to avoid division by zero. Rebalance every 21 completed trading sessions. Decisions must use only returns before the held session. No optimization based on subsequent returns is allowed.

## Mathematical conventions

- Daily adjusted-price-claimed return: \(r_{i,t} = P_{i,t}/P_{i,t-1} - 1\).
- Gross portfolio return: \(r^g_{p,t} = \sum_i w_{i,t}^{pre} r_{i,t}\).
- Turnover cost approximation: \(c_t = 0.0008 \sum_i |w_{i,t}^{target} - w_{i,t}^{drift}|\).
- Portfolio net return approximation: \(r^{net}_{p,t} = r^g_{p,t} - c_t\) in the archived rule evaluator. Compounding and position drift are separate. This cost approximation is not the exact financed-and-settled accounting of a broker.
- NAV: \(\mathrm{NAV}_t = \prod_{s\leq t}(1+r^{net}_{p,s})\).
- Geometric annual return: \(\mathrm{NAV}_{end}^{252/N} - 1\).
- Max drawdown: \(\min_t \big(\mathrm{NAV}_t/\max_{s\leq t}\mathrm{NAV}_s-1\big)\), peak initialized at original equity of 1.
- Empirical historical VaR at 95%: the left-tail loss quantile. Expected shortfall: mean loss of the worst 5% observed sessions. These are **unconditional historical descriptive** tail summaries.

## Conditional risk-model diagnostics

Historical VaR forecast for t uses an empirical quantile from the previous W observations. Gaussian EWMA models conditional variance recursively with a fixed 0.94 decay and assumes zero conditional mean and Gaussian one-day innovation. Both use past observations only. Compare observed exception counts with nominal 99% VaR loss probability 1%; report conditional-coverage/independence diagnostics. Thin tails and rare breaches can make p-values unreliable.

## Historical events vs scenarios

Ex-post COVID 2020 shock and 2022 duration repricing are **historical replay periods**—actual realized simulation returns between the named dates. Separately, an RFQ hypothetical shock matrix applies invented instantaneous shocks. Do not combine these into a single narrative of empirical 2026 forecasting skill.

## Statistical scope

Intervals use contemporaneously paired block bootstrap draws (circular 21-session blocks), with 95% empirical percentiles of the annualized daily mean return difference between the rule and *costed* SPY. They are **not** confidence intervals for CAGR difference; they also do not correct multiple testing or model search. The 2023–2025 segment is retrospective because it was already read; it cannot be called a held-out independent test. A future study requires a preregistered untouched time interval and documented strategy governance.

## Limitations

Data-provider adjusted-price claim unverified; possible hindsight selection of surviving ETFs; fee constant is not independently measured; cash return assumed zero in reference Sharpe; no tax, borrow/short, cash collateral, duration convexity, FX hedging or real execution; nonstationary volatility and risk calibration limits. Fully transparent underperformance against SPY is a valid research result.
