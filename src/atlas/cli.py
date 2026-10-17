"""CLI: atlas --source synthetic --output results/"""
from __future__ import annotations
import argparse
from .data import TICKERS, load_csv, price_returns, synthetic_prices, yahoo_prices
from .backtest import run_backtest
from .report import write_reports


def main() -> None:
    p = argparse.ArgumentParser(description="ATLAS reproducible cross-asset research lab")
    p.add_argument("--source", choices=["synthetic", "csv", "yahoo"], default="synthetic")
    p.add_argument("--csv", help="CSV with Date and adjusted-close price columns")
    p.add_argument("--start", default="2015-01-01", help="Yahoo observation start")
    p.add_argument("--end", default=None, help="Yahoo observation end (exclusive)")
    p.add_argument("--strategy", choices=["equal", "inverse_vol", "momentum", "regime", "cvar"], default="regime")
    p.add_argument("--rebalance", type=int, default=21)
    p.add_argument("--fee-bps", type=float, default=3.0)
    p.add_argument("--slippage-bps", type=float, default=5.0)
    p.add_argument("--output", default="results")
    p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--run-ml", action="store_true", help="Optional expanding walk-forward downside classification study")
    p.add_argument("--freeze-data", action="store_true", help="Save checked SHA256 data snapshot with source manifest")
    p.add_argument("--evaluate", action="store_true", help="Compare fixed strategies in chronological holdout")
    p.add_argument("--test-start", default=None, help="First session in test, ISO date; defaults to final 25% of returns")
    p.add_argument("--bootstrap-reps", type=int, default=500)
    p.add_argument("--trade-demo", action="store_true", help="Generate illustrative risk-limit trade decision memo")
    args = p.parse_args()
    if args.source == "csv":
        if not args.csv:
            p.error("--csv is required with --source csv")
        prices = load_csv(args.csv)
        provenance = f"USER CSV: {args.csv} (must contain adjusted prices)"
    elif args.source == "yahoo":
        prices = yahoo_prices(TICKERS, start=args.start, end=args.end)
        provenance = f"THIRD-PARTY YAHOO MARKET PRICES ({args.start} onward; verify provenance)"
    else:
        prices = synthetic_prices(seed=args.seed)
        provenance = f"SYNTHETIC GENERATED DATA (seed={args.seed}, NOT REAL RETURNS)"
    from pathlib import Path
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    if args.freeze_data:
        from .provenance import snapshot_prices, verify_snapshot
        manifest = snapshot_prices(prices, provenance, out / "frozen_data")
        verify_snapshot(out / "frozen_data")
        print(f"Verified dataset SHA256: {manifest['sha256']}")
    returns = price_returns(prices)
    bt = run_backtest(returns, strategy=args.strategy,
                      rebalance_every=args.rebalance,
                      fee_bps=args.fee_bps, slippage_bps=args.slippage_bps)
    report = write_reports(returns, bt, args.output, provenance)
    print(f"ATLAS complete: {args.output} | {provenance}")
    print(f"Strategy: {args.strategy} | current heuristic regime: {report['regime']['label']}")
    print(f"Historical 1d 95% VaR: {report['strategy']['historical_var_95_1d']:.2%}")
    if args.evaluate:
        from .evaluation import evaluate_fixed_strategies, write_evaluation
        cutoff = args.test_start or str(returns.index[int(len(returns) * .75)].date())
        eval_result = evaluate_fixed_strategies(returns, cutoff, repetitions=args.bootstrap_reps,
                                               fee_bps=args.fee_bps, slippage_bps=args.slippage_bps,
                                               rebalance_every=args.rebalance)
        write_evaluation(eval_result, out / "evaluation")
        print(f"Fixed-date comparison generated: {cutoff}; {len(eval_result.summary)} candidate rules")
        print("RESEARCH WARNING: results seen after test inspection cannot be treated as untouched holdout.")
    if args.trade_demo:
        from .desk import decide_trade, write_decision_memo, RiskLimits
        import pandas as pd
        w = pd.Series(0.0, index=returns.columns)
        if "SPY" not in w.index or "BIL" not in w.index:
            p.error("--trade-demo requires SPY and BIL price series")
        w["SPY"], w["BIL"] = .50, .50
        limit = RiskLimits()
        decision, _ = decide_trade(w, returns, float(prices["SPY"].iloc[-1]),
                                   ticker="SPY", side="buy", notional_usd=20_000,
                                   nav_usd=1_000_000, assumed_adv_usd=5_000_000,
                                   limits=limit)
        write_decision_memo(decision, limit, out / "example_trade_decision",
                            provenance, str(returns.index[-1].date()))
        print(f"Example risk gate: {decision.decision}; reasons: {decision.reasons}")
    if args.run_ml:
        from pathlib import Path
        from .ml import walk_forward_downside
        ml = walk_forward_downside(prices)
        path = Path(args.output)
        ml.predictions.to_csv(path / "walk_forward_predictions.csv", index_label="Date")
        (path / "ml_validation.txt").write_text(
            f"{ml.label}\n"
            f"OOS samples: {len(ml.predictions)}; events: {ml.number_events}\n"
            f"Model Brier score: {ml.brier_model:.6f}\n"
            f"Expanding base rate Brier score: {ml.brier_baseline:.6f}\n"
            "Lower is better. If model Brier is higher, it underperformed base rate.\n"
            "Historical, correlated overlapping 5-session outcomes; synthetic data is illustrative only.\n",
            encoding="utf-8")
        print(f"ML validation: model Brier={ml.brier_model:.4f}, base rate={ml.brier_baseline:.4f}")
    print("IMPORTANT: Demonstration ≠ verified alpha, execution, or investment advice.")

if __name__ == "__main__":
    main()
