"""Optional interactive research interface. Run: streamlit run app.py"""
from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from atlas.data import TICKERS, synthetic_prices, yahoo_prices, price_returns
from atlas.backtest import run_backtest
from atlas.risk import performance_stats, historical_var_es, stress_portfolio, risk_contributions
from atlas.rfq import simulate_rfq
from atlas.desk import RiskLimits, decide_trade
from atlas.strategies import market_regime

st.set_page_config(page_title="ATLAS Trading Desk", page_icon="📈", layout="wide")
st.title("ATLAS | Cross-Asset Trading & Risk Intelligence")
st.caption("Academic market risk / strategy research simulator. No live execution, broker link or institutional pricing.")

with st.sidebar:
    st.header("Research settings")
    source = st.selectbox("Data source", ["Synthetic demonstration", "Pinned historical ETF archive (2018–2025)", "CSV uploaded adjusted closes", "Yahoo research data"])
    # Regime policy uses IEF/BIL/GLD that are absent from the three-ticker archive.
    supported = ["inverse_vol", "equal", "cvar"] if source.startswith("Pinned") else ["regime", "momentum", "inverse_vol", "equal", "cvar"]
    strategy = st.selectbox("Allocation strategy", supported)
    capital = st.number_input("Portfolio NAV ($)", min_value=1000., value=1_000_000., step=100_000.)
    rebalance = st.slider("Rebalance frequency (sessions)", 5, 63, 21)
    fee = st.slider("Commissions (bps)", 0, 30, 3)
    slip = st.slider("Slippage assumption (bps)", 0, 50, 5)
    seed = st.number_input("Synthetic random seed", min_value=0, value=2026)
    csv = st.file_uploader("CSV: Date, SPY, ... adjusted close prices", type=["csv"]) if source.startswith("CSV") else None

@st.cache_data(show_spinner=False)
def get_prices(src, seed_value):
    if src.startswith("Pinned"):
        from atlas.real_study import read_pinned_market_data
        prices, provenance = read_pinned_market_data()
        return prices
    if src.startswith("Synthetic"):
        return synthetic_prices(seed=int(seed_value))
    if src.startswith("Yahoo"):
        return yahoo_prices(TICKERS, start="2015-01-01")
    raise ValueError("Upload your adjusted-close file")

try:
    if source.startswith("CSV"):
        if csv is None:
            st.info("Upload your own adjusted-close wide-format CSV to begin.")
            st.stop()
        from atlas.data import validate_prices
        prices = pd.read_csv(csv)
        prices["Date"] = pd.to_datetime(prices["Date"])
        prices = validate_prices(prices.set_index("Date"))
    else:
        prices = get_prices(source, seed)
    returns = price_returns(prices)
    bt = run_backtest(returns, strategy=strategy, rebalance_every=rebalance,
                      fee_bps=fee, slippage_bps=slip)
    stats = performance_stats(bt.daily_returns)
    regime = market_regime(returns)
    weights = bt.weights.iloc[-1]
except Exception as error:
    st.error(f"Dataset or simulation failed: {error}")
    st.stop()

if source.startswith("Pinned"):
    st.info("PINNED HISTORICAL OBSERVATIONS: archived SPY, QQQ, TLT from 2018–2025. Archive price adjustments and data licensing have not been independently verified; the strategy comparison is retrospective, NOT a pristine holdout.")
elif source.startswith("Synthetic"):
    st.warning("SYNTHETIC DEMONSTRATION: These are computer-generated assets, not historical returns. Do not cite synthetic performance on a CV.")
else:
    st.info("Research data: use only in accordance with feed licensing; no look-ahead-safe macro vintages or live executable quotes are implied.")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Heuristic market regime", regime["label"])
k2.metric("Historical 1d VaR 95%", f"{stats['historical_var_95_1d']:.2%}")
k3.metric("Expected Shortfall 95%", f"{stats['historical_es_95_1d']:.2%}")
k4.metric("Max drawdown", f"{stats['max_drawdown']:.1%}")

market_tab, risk_tab, rfq_tab, validation_tab, ml_tab = st.tabs(["Strategy research", "Portfolio risk & events", "Simulated RFQ", "Risk model validation", "ML out-of-sample"])

with market_tab:
    baseline = (1 + returns["SPY"]).cumprod() if "SPY" in returns else (1+returns.iloc[:,0]).cumprod()
    fig = go.Figure()
    fig.add_scatter(x=bt.equity.index, y=bt.equity.values, name="ATLAS after costs", mode="lines")
    fig.add_scatter(x=baseline.index, y=baseline.values, name="SPY price-return proxy", mode="lines")
    fig.update_layout(title="Growth of one unit of capital", xaxis_title="Session", yaxis_title="Equity multiple")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(pd.DataFrame({"strategy": stats, "SPY baseline": performance_stats(returns["SPY"]) if "SPY" in returns else performance_stats(returns.iloc[:,0])}), use_container_width=True)
    st.caption("SPY baseline excludes transaction fees, benchmark financing, and potential distribution differences; returns are from supplied adjusted closing prices.")
    st.metric("Total sum of daily turnover", f"{bt.turnover.sum():.2f}× NAV")

with risk_tab:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Current holdings")
        st.dataframe(weights.rename("Portfolio weight").to_frame().style.format("{:.2%}"), use_container_width=True)
    with c2:
        st.subheader("Euler volatility contributions")
        st.dataframe(risk_contributions(returns, weights).style.format("{:.2%}"), use_container_width=True)
    st.subheader("Single-step hypothetical market shocks")
    st.dataframe(stress_portfolio(weights, capital).style.format({"portfolio_return": "{:.2%}", "estimated_pnl_usd": "${:,.0f}"}), use_container_width=True)
    st.caption("Shocks are hypothetical and not historical realized crises or confidence intervals.")
    from atlas.historical_events import replay_event_windows
    if not source.startswith("Synthetic"):
        events = replay_event_windows(pd.DataFrame({"ATLAS strategy (net)":bt.daily_returns,
            "SPY reference (gross)":returns["SPY"] if "SPY" in returns else returns.iloc[:,0]}))
        st.subheader("Ex-post event windows (unverified for uploaded CSV)")
        if len(events):
            show = events[["event", "asset_or_strategy", "sessions", "cumulative_return", "worst_peak_to_trough"]].copy()
            st.dataframe(show.style.format({"cumulative_return": "{:+.2%}", "worst_peak_to_trough":"{:.2%}"}),
                use_container_width=True)
            st.caption("Model-return window replays, selected with hindsight. For uploaded CSV, historical event authenticity is NOT established. Not forecasts or actual executable trades.")
        else:
            st.info("No named event window with sufficient observations in these prices.")

with rfq_tab:
    st.subheader("Illustrative trade pricing and inventory impact")
    candidates = [x for x in weights.index if x != "BIL"]
    t = st.selectbox("Instrument", candidates)
    side = st.radio("Portfolio action", ["sell", "buy"], horizontal=True)
    notion = st.number_input("Trade notional ($)", min_value=1000., value=20_000., step=5_000.)
    adv = st.number_input("Assumed daily traded notional ($)", min_value=100_000., value=50_000_000., step=1_000_000.)
    try:
        rfq = simulate_rfq(weights, returns, latest_mid=float(prices[t].iloc[-1]),
                           ticker=t, side=side, notional_usd=notion,
                           nav_usd=capital, assumed_adv_usd=adv)
        a, b, c = st.columns(3)
        a.metric("Reference adjusted close (NOT tradable mid)", f"${rfq.mid_reference:.2f}")
        b.metric("Hypothetical quote", f"${rfq.simulated_quote:.2f}")
        c.metric("Hypothetical quote adjustment", f"{rfq.total_markup_bps:.1f} bps")
        st.write(f"95% historical VaR dollars: **${rfq.before_var95_usd:,.0f} → ${rfq.after_var95_usd:,.0f}**")
        compare = pd.DataFrame({"before": rfq.before_stress["estimated_pnl_usd"],
                                "after": rfq.after_stress["estimated_pnl_usd"]})
        st.dataframe(compare.style.format("${:,.0f}"), use_container_width=True)
        st.caption("Pricing parameters, assumed liquidity and market impact are invented demonstration inputs. No tradable quotes or bank-specific inventory model.")
        st.markdown("#### Portfolio risk approval (demonstration only)")
        decision, _ = decide_trade(weights, returns, float(prices[t].iloc[-1]),
                                   ticker=t, side=side, notional_usd=notion,
                                   nav_usd=capital, assumed_adv_usd=adv,
                                   limits=RiskLimits(max_position_fraction=.60,
                                                    max_var95_usd=capital*.03,
                                                    max_stress_loss_usd=capital*.12,
                                                    max_daily_adv_participation=.02,
                                                    max_incremental_var95_usd=capital*.008))
        st.write(f"**Risk-gate decision: {decision.decision}**")
        for reason in decision.reasons:
            st.write(f"• {reason}")
        st.caption("Limits are educational constants. Passing is not an institutional authorization.")
    except ValueError as error:
        st.info(f"Trade cannot be simulated under long-only funded constraints: {error}")

with validation_tab:
    st.write("Daily 99% value-at-risk forecasts are computed using only previous observations. This is a risk-model diagnostic, not evidence of profitable strategy prediction.")
    window = st.slider("Rolling calibration window (past sessions)", 90, 504, 252, 21)
    if st.button("Backtest historical-simulation and Gaussian EWMA VaR", key="run_validation"):
        try:
            from atlas.institutional_risk import rolling_risk_validation
            out = rolling_risk_validation(bt.daily_returns, window=window, confidence=.99)
            st.dataframe(out.diagnostics.drop(columns=["transitions", "warning"], errors="ignore"), use_container_width=True)
            model_chart = out.forecasts[["loss", "var_historical", "var_ewma_gaussian"]].tail(500)
            st.line_chart(model_chart)
            st.caption("Kupiec and Christoffersen large-sample p-values have weak power when rare tail events are sparse. Model validity is not certified by one test.")
        except Exception as error:
            st.warning(f"Risk validation unavailable: {error}")

with ml_tab:
    st.write("Experimental 5-session downside-event classifier, expanding walk-forward retraining, purged future labels, compared against an expanding base-rate benchmark.")
    if st.button("Run optional out-of-sample ML analysis"):
        try:
            from atlas.ml import walk_forward_downside
            with st.spinner("Training and testing historical windows..."):
                ml = walk_forward_downside(prices)
            st.metric("Model Brier score (lower better)", f"{ml.brier_model:.4f}")
            st.metric("Expanding base-rate Brier score", f"{ml.brier_baseline:.4f}")
            st.write(f"Out-of-sample event observations: {ml.number_events} / {len(ml.predictions)}")
            st.line_chart(ml.predictions[["probability", "expanding_base_rate"]])
            st.dataframe(ml.predictions.tail(50), use_container_width=True)
            st.caption("Overlapping future 5-session labels; probabilities may be uncalibrated. Be skeptical if model fails to beat baseline.")
        except Exception as error:
            st.warning(f"Optional ML analysis unavailable: {error} (pip install -e '.[ml]')")
