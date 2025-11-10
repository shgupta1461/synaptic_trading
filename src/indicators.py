import numpy as np
import pandas as pd


def moving_average(series: pd.Series, window: int) -> float:
    """Compute simple moving average."""
    if len(series) < window:
        return np.nan
    return float(series.tail(window).mean())


def compute_rsi(series: pd.Series, period: int = 14) -> float:
    """Compute RSI(14) using Wilder’s method."""
    if len(series) < period + 1:
        return np.nan

    delta = series.diff().dropna()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)

    avg_gain = gains.rolling(period).mean().iloc[-1]
    avg_loss = losses.rolling(period).mean().iloc[-1]

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def trading_decision(ma20, ma50, rsi):
    """Rule: BUY if MA20>MA50 & RSI<70, SELL if MA20<MA50 & RSI>30."""
    if np.isnan(ma20) or np.isnan(ma50) or np.isnan(rsi):
        return "HOLD"
    if ma20 > ma50 and rsi < 70:
        return "BUY"
    elif ma20 < ma50 and rsi > 30:
        return "SELL"
    return "HOLD"
