# ATLAS | Development Roadmap

ATLAS v1.2 provides a documented engineering system; it is **not** a deployed trading desk or an independently validated profitable strategy. Prioritize scientific integrity over inflated backtest returns.

## Shipped

1. Read archived ETF prices with fixed source commit and per-file Git blob SHA checks. Remote and offline local-pinned-directory paths are supported.
2. Portfolio rules with explicit dated holdings, cost and turnover assumptions, plus cost-aligned buy-and-hold comparator.
3. Historical risk windows, rolling 99% VaR coverage diagnostics, expected shortfall, and circular paired block-bootstrap uncertainty estimates.
4. Executable risk-limit and simulated dealer quote demos, Streamlit visualization, tests and CI.
5. Published past historical reference aggregates and research integrity notes; separate synthetic fixtures and results.
6. Manually triggered GitHub Actions empirical audit, which fails on hash or reference disagreement and publishes derived aggregate reports as a CI artifact.

## Next scientifically necessary steps

- Independently reconcile adjusted prices, distributions and splits with a properly licensed vendor.
- Freeze a preregistered rule set before obtaining **future** test observations; prior 2023–2025 retrospectives are already observed.
- Validate real executable bid-ask quotes, liquidity, market impact and financing rather than relying on fixed assumed costs.
- Add macroeconomic data release vintages; avoid using revised values at historical decision times.
- Extend from proxies to instrument-specific sensitivities, duration, yield curve, factor decomposition and hedge accounting where rights permit.

**Publication standard:** Never treat code quality, 38+ unit tests, or historical simulation as proof of forecast accuracy or alpha.
