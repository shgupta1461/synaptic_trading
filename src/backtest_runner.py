from __future__ import annotations
import math
from dataclasses import dataclass
import numpy as np
import pandas as pd

# Track A: correct import per the primer
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.config import BacktestEngineConfig

from src.indicators import moving_average, compute_rsi, trading_decision


@dataclass
class BacktestParams:
    seed: int = 42
    start_cash: float = 100_000.0
    size: int = 1                      # 1 unit per trade
    tick_size: float = 0.01            # fixed 1-tick slippage size
    prob_slippage: float = 0.5         # 50% chance to slip by 1 tick (bar/L1-like)
    fees_bps: float = 1.0              # ~1 bps per executed side
    adaptive_hilo: bool = False        # keep deterministic O->H->L->C by default
    eod_flatten: bool = True


def _round_to_tick(px: float, tick: float) -> float:
    if tick <= 0:
        return float(px)
    q = round(px / tick)
    # keep decimals consistent with tick size (0.01 -> 2 dp)
    dp = max(0, -int(round(math.log10(tick)))) if tick < 1 else 0
    return round(q * tick, dp)


def _bar_path(o, h, l, c, adaptive=False):
    # As per docs: fixed O->H->L->C or adaptive ordering.
    if not adaptive:
        return [("open", o), ("high", h), ("low", l), ("close", c)]
    # simple adaptive heuristic (still deterministic)
    return (
        [("open", o), ("high", h), ("low", l), ("close", c)]
        if abs(o - h) < abs(o - l)
        else [("open", o), ("low", l), ("high", h), ("close", c)]
    )


def _fee(amount_notional: float, bps: float) -> float:
    # fees charged per executed side: notional * (bps / 10_000)
    return abs(amount_notional) * (bps / 10_000.0)


def _load_bars(csv_path="data/ohlcv.csv") -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df = df.dropna(subset=["close"]).copy()
    # Bars must be timestamped on CLOSE per Nautilus docs. If your file is open-stamped,
    # shift by one bar here: df["timestamp"] += pd.Timedelta(minutes=1)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


def run_backtest_nautilus_trackA(
    csv_path: str = "data/ohlcv.csv",
    output_equity_csv: str = "data/equity_curve.csv",
    params: BacktestParams = BacktestParams(),
):
    """
    Track A (low-level): Backtest MA(20/50)+RSI(14) with:
      - 1-tick fixed slippage (probabilistic, bar/L1-style)
      - ~1 bps fees on each executed side
      - O->H->L->C price sequencing (deterministic) per docs
    Produces: trades, equity curve CSV, final equity, max DD, daily Sharpe.
    """
    rng = np.random.RandomState(params.seed)

    # Minimal BacktestEngine usage (correct import, config)
    engine = BacktestEngine(config=BacktestEngineConfig(trader_id="CAND-TRACKA-001"))

    df = _load_bars(csv_path)

    closes = []
    position = 0              # -1, 0, +1
    entry = None
    cash = float(params.start_cash)
    size = params.size
    tick = params.tick_size

    trades = []
    equity = []

    def market_fill(base_px: float, side: int) -> float:
        """Apply 1-tick adverse slippage with given probability (bar/L1 behavior)."""
        slip = tick if rng.rand() < params.prob_slippage else 0.0
        px = base_px + slip if side > 0 else base_px - slip
        return _round_to_tick(px, tick)

    for row in df.itertuples(index=False):
        # Indicator snapshot uses data up to *previous* close to avoid look-ahead
        closes.append(row.close)
        series = pd.Series(closes)
        ma20 = moving_average(series, 20)
        ma50 = moving_average(series, 50)
        rsi = compute_rsi(series)

        decision = trading_decision(ma20, ma50, rsi)

        # Build bar price path per docs
        path = _bar_path(row.open, row.high, row.low, row.close, adaptive=params.adaptive_hilo)

        if decision == "BUY" and position <= 0:
            # Close short if any
            if position == -1 and entry is not None:
                px = market_fill(path[0][1], side=+1)
                cash += (entry - px) * size
                cash -= _fee(px * size, params.fees_bps)
                trades.append(("COVER", row.timestamp.isoformat(), float(px), size))
            # Open long
            px = market_fill(path[0][1], side=+1)
            cash -= _fee(px * size, params.fees_bps)
            position = +1
            entry = float(px)
            trades.append(("BUY", row.timestamp.isoformat(), float(px), size))

        elif decision == "SELL" and position >= 0:
            # Close long if any
            if position == +1 and entry is not None:
                px = market_fill(path[0][1], side=-1)
                cash += (px - entry) * size
                cash -= _fee(px * size, params.fees_bps)
                trades.append(("SELL", row.timestamp.isoformat(), float(px), size))
            # Open short
            px = market_fill(path[0][1], side=-1)
            cash -= _fee(px * size, params.fees_bps)
            position = -1
            entry = float(px)
            trades.append(("SHORT", row.timestamp.isoformat(), float(px), size))

        # Mark-to-market on bar close
        mtm = row.close
        if entry is None:
            eq = cash
        else:
            eq = cash + position * (mtm - entry) * size
        equity.append(eq)

    # End-of-day flatten
    if params.eod_flatten and position != 0 and entry is not None:
        last_close = df["close"].iloc[-1]
        side = -1 if position > 0 else +1
        px = market_fill(last_close, side=side)
        if position == +1:
            cash += (px - entry) * size
            trades.append(("EOD_SELL", df["timestamp"].iloc[-1].isoformat(), float(px), size))
        else:
            cash += (entry - px) * size
            trades.append(("EOD_COVER", df["timestamp"].iloc[-1].isoformat(), float(px), size))
        cash -= _fee(px * size, params.fees_bps)
        position, entry = 0, None
        equity[-1] = cash

    # Equity curve & metrics
    eq_df = pd.DataFrame({"timestamp": df["timestamp"], "equity": equity})
    eq_df.to_csv(output_equity_csv, index=False)

    rets = eq_df["equity"].pct_change().replace([np.inf, -np.inf], np.nan).dropna()
    sharpe = (rets.mean() / (rets.std(ddof=1) + 1e-12)) * math.sqrt(252) if len(rets) > 3 else 0.0
    cummax = eq_df["equity"].cummax()
    drawdown = (eq_df["equity"] - cummax) / cummax.replace(0, np.nan)
    max_dd = float(drawdown.min()) if len(drawdown) else 0.0

    result = {
        "trades": trades,
        "final_equity": float(eq_df["equity"].iloc[-1]),
        "max_drawdown": round(max_dd, 6),
        "daily_sharpe": round(float(sharpe), 4),
        "equity_curve": eq_df,
    }

    print(
        f"T2 Track-A Results → "
        f"Equity: {result['final_equity']:.2f}, "
        f"MaxDD: {result['max_drawdown']:.3%}, "
        f"Sharpe: {result['daily_sharpe']:.2f}"
    )
    return result


if __name__ == "__main__":
    run_backtest_nautilus_trackA()
