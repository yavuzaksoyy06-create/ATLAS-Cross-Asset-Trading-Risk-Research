"""Point-in-time, purged walk-forward downside probability research.

IMPORTANT: This is an experimental research model. Do not interpret its
probabilities as calibrated or its performance as tested without inspecting
out-of-sample results against the expanding base-rate benchmark.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd
from .data import validate_prices


@dataclass
class MLResult:
    predictions: pd.DataFrame
    brier_model: float
    brier_baseline: float
    number_events: int
    label: str


def make_features(prices: pd.DataFrame, primary: str = "SPY", horizon: int = 5,
                  drawdown_threshold: float = -.03) -> tuple[pd.DataFrame, pd.Series]:
    """Features available at close t; label uses ONLY t+1..t+horizon.

    No unreleased macro series, revised macro observations, or forward filled prices.
    """
    if primary not in prices or horizon < 1:
        raise ValueError("Invalid target ticker or prediction horizon.")
    prices = validate_prices(prices, minimum_assets=1)
    closes = prices[primary]
    daily = closes.pct_change(fill_method=None)
    X = pd.DataFrame(index=prices.index)
    for days in [5, 21, 63, 126]:
        X[f"{primary}_ret_{days}d"] = closes.pct_change(days, fill_method=None)
    for days in [21, 63]:
        X[f"{primary}_vol_{days}d"] = daily.rolling(days).std() * np.sqrt(252)
    for ticker in ["QQQ", "IEF", "TLT", "GLD", "HYG", "UUP"]:
        if ticker in prices:
            X[f"{ticker}_ret_21d"] = prices[ticker].pct_change(21, fill_method=None)
    forward_return = closes.shift(-horizon) / closes - 1
    y = (forward_return <= drawdown_threshold).astype(float)
    y[forward_return.isna()] = np.nan
    return X, y


def walk_forward_downside(prices: pd.DataFrame, horizon: int = 5,
                          minimum_training: int = 252,
                          retrain_interval: int = 21,
                          threshold: float = -.03) -> MLResult:
    """Refit on expanding, fully labelled past at each retrain point.

    At forecast close index i, only features j<=i and labels j+h<=i are known.
    It is conservative about data timing; no future knowledge enters training.
    """
    try:
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import brier_score_loss
    except ImportError as exc:
        raise ImportError("Install ML dependencies with pip install -e '.[ml]'") from exc
    if minimum_training < 100 or retrain_interval < 1 or len(prices) < minimum_training + 140:
        raise ValueError("Need sufficient history beyond minimum training period.")
    X, y = make_features(prices, horizon=horizon, drawdown_threshold=threshold)
    model = None
    baseline = np.nan
    results = []
    first_prediction_i = max(minimum_training + horizon + 126, 200)
    for i in range(first_prediction_i, len(prices) - horizon):
        if model is None or (i - first_prediction_i) % retrain_interval == 0:
            # At end of day i, label at observation j is known only if j+h<=i.
            end_exclusive = i - horizon + 1
            train_X = X.iloc[:end_exclusive].dropna()
            train_X = train_X.loc[train_X.index.intersection(y.dropna().index)]
            train_y = y.loc[train_X.index].astype(int)
            if len(train_X) < minimum_training or train_y.nunique() < 2:
                model = None
                continue
            baseline = float(train_y.mean())
            model = make_pipeline(StandardScaler(), LogisticRegression(C=.25, max_iter=1000))
            model.fit(train_X, train_y)
        features_today = X.iloc[[i]]
        if model is None or features_today.isna().any().any():
            continue
        pred = float(model.predict_proba(features_today)[0, 1])
        results.append((X.index[i], pred, baseline, int(y.iloc[i])))
    if len(results) < 30:
        raise ValueError("Insufficient labelled out-of-sample predictions or events.")
    oos = pd.DataFrame(results, columns=["Date", "probability", "expanding_base_rate", "actual_event"]).set_index("Date")
    return MLResult(predictions=oos,
                    brier_model=float(brier_score_loss(oos.actual_event, oos.probability)),
                    brier_baseline=float(brier_score_loss(oos.actual_event, oos.expanding_base_rate)),
                    number_events=int(oos.actual_event.sum()),
                    label=f"{horizon}-day {threshold:.0%} or worse forward { 'SPY' } return")
