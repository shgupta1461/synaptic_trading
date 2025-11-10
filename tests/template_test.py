from pathlib import Path
import csv
import pandas as pd
from fastapi.testclient import TestClient
from src.main import app, consumer
from src.indicators import moving_average, compute_rsi, trading_decision

BASE = Path(__file__).resolve().parents[1]


def test_csv_has_expected_columns():
    csv_path = BASE / "data" / "ohlcv.csv"
    assert csv_path.exists(), "ohlcv.csv missing"
    with open(csv_path, "r") as f:
        reader = csv.reader(f)
        headers = next(reader)
    for col in ["timestamp", "open", "high", "low", "close", "volume"]:
        assert col in headers


def test_indicators_basic():
    s = pd.Series(range(1, 60))
    assert round(moving_average(s, 20), 2) == round(s.tail(20).mean(), 2)
    rsi = compute_rsi(s)
    assert 0 <= rsi <= 100
    assert trading_decision(60, 50, 40) == "BUY"


def test_get_signal(monkeypatch):
    monkeypatch.setattr(consumer, "get_prices", lambda symbol: pd.Series(range(1, 60)))
    client = TestClient(app)
    r = client.get("/signal?symbol=XYZ")
    assert r.status_code == 200
    data = r.json()
    assert "rsi" in data and "decision" in data


from src.backtest_runner import run_backtest_nautilus_trackA, BacktestParams

def test_equity_curve_deterministic_trackA():
    p = BacktestParams(seed=123, prob_slippage=0.5, fees_bps=1.0)
    r1 = run_backtest_nautilus_trackA(params=p)
    r2 = run_backtest_nautilus_trackA(params=p)
    assert abs(r1["final_equity"] - r2["final_equity"]) < 1e-9
    assert r1["max_drawdown"] == r2["max_drawdown"]
    assert r1["daily_sharpe"] == r2["daily_sharpe"]
