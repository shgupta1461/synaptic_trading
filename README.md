````markdown
# Synaptic Trading — Technical Evaluation (November 2025)

This repository contains my complete solution for the **Synaptic Trading AI-First Technical Evaluation**.  
It implements the end-to-end tasks **T1 → T4**, including async data streaming, backtesting with NautilusTrader, SQL modeling, and a microstructure learning sprint.

---

## Quick Run
```bash
# clone and run tests
git clone https://github.com/<your-username>/synaptic_trading.git
cd synaptic_trading
pip install -r requirements.txt
pytest -v
python -m src.backtest_runner
```
---

### 🧾 **Top Summary**

| Field | Details |
|-------|----------|
| **GitHub Repo** | [https://github.com/shgupta1461/synaptic_trading](https://github.com/shgupta1461/synaptic_trading) |
| **Quick Run Commands** | `pytest -v && python -m src.backtest_runner` |
| **Environment** | Python 3.13.1, NautilusTrader 1.221.0, FastAPI 0.115+, Pandas 2.3.3, Windows 11 |
| **Phase-1 Time Log** | ~5h 45m total (within 6-hour cap) |
| **AI Tools Used** | ChatGPT (GPT-5) — for scaffolding code, documentation, and validation steps. All outputs verified manually. |

---

## 📂 Project Structure

| Path / File | Description |
|--------------|-------------|
| `src/main.py` | FastAPI microservice consuming an async tick stream (`stream_stub.py`) — Task T1 |
| `src/backtest_runner.py` | NautilusTrader-based backtesting runner (MA20/50 + RSI14) — Task T2 (Track A) |
| `tests/template_test.py` | Pytest suite verifying CSV schema, indicator correctness, and deterministic equity curve |
| `data/ohlcv.csv` | 1-minute OHLCV data with intentional gaps/outliers |
| `VERIFICATION.md` | Consolidated verification steps and results |
| `requirements.txt` | Python dependencies |
| `README.md` | This document |

---

## ⚙️ Setup & Installation

### 1️⃣ Create and activate virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate     # On Windows
# source .venv/bin/activate   # On macOS/Linux
````

### 2️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🚀 Run Instructions

### ▶️ 1. Start the FastAPI Service (T1)

Runs the tick-streaming microservice using simulated price data.

```bash
uvicorn src.main:app --reload
```

You should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

---

### 📈 2. Run the Nautilus Backtest (T2 — Track A)

CORRECT IMPORT USED: 
```python 
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.config import BacktestEngineConfig
```

Implements MA(20/50) crossover + RSI(14) strategy with 1 bps fee, 1-tick slippage, and EOD flat logic.

```bash
python src/backtest_runner.py
```

**Expected Output (sample):**

```
T2 Track-A Results → Equity: 99994.64, MaxDD: -0.015%, Sharpe: -0.37
```

---

### ✅ 3. Run All Tests (Verification)

Checks reproducibility, CSV structure, and indicator correctness.

```bash
pytest -v
```

**Expected Result:**

```
============================ 4 passed, 2 warnings in 2.65s =============================
```

Warnings related to `FastAPI @app.on_event("startup")` can be safely ignored —
they are just deprecation notices.

---

## 🧠 SQL Design & Data Modeling (T3)

See [`VERIFICATION.md`](./VERIFICATION.md) for:

* Normalized, partitioned PostgreSQL schema for bars, trades, orders, positions, and PnL.
* Analytical queries:

  * Daily PnL rollup & max drawdown
  * Last known position per symbol
  * 30-day rolling Sharpe ratio
* Scaling plan using **monthly partitions** + **BRIN indexes** for 100× data growth.

---

## 📘 Learning Sprint: Microstructure & Options (T4)

See [`VERIFICATION.md`](./VERIFICATION.md) for:

* Failure mode: **bar timestamp look-ahead bias** and mitigation.
* Probabilistic slippage model (1–2 tick adverse, queue-based).
* Pre-live **options spread** sanity checks:

  * Assignment/early exercise handling
  * Carry & margin treatment
  * Liquidity and slippage realism.

---

## 🧪 Verification Summary

| Phase            | Description                                             | Status                |
| ---------------- | ------------------------------------------------------- | --------------------- |
| **T1**           | FastAPI microservice and async tick stream              | ✅ Operational         |
| **T2 (Track A)** | NautilusTrader backtest engine (MA20/50 + RSI14)        | ✅ Equity reproducible |
| **T3**           | PostgreSQL schema, analytical queries, and scaling plan | ✅ Documented          |
| **T4**           | Microstructure + options learning sprint                | ✅ Completed           |
| **Tests**        | Deterministic equity + schema validation                | ✅ All passed          |

---

## 🧾 One-Command Reproducibility

```bash
pytest -v && python src/backtest_runner.py
```

Runs all tests and backtest end-to-end.

---

## 💾 Example Folder Layout

```
synaptic_trading/
│
├── src/
│   ├── main.py
│   └── backtest_runner.py
│   └── consumer.py
│   └── indicator.py
│
├── tests/
│   ├── template_test.py
│   └── conftest.py
│
├── data/
│   └── ohlcv.csv
│   └── equity_curve.py
│
├── VERIFICATION.md
├── requirements.txt
└── README.md
```

---

## 📈 Results Snapshot

| Metric               | Value                        |
| -------------------- | ---------------------------- |
| **Final Equity**     | 99,994.64                    |
| **Max Drawdown**     | -0.015%                      |
| **Sharpe (daily)**   | -0.37                        |
| **Trades Simulated** | Deterministic & reproducible |

---

## 🔒 Verification Notes

* Verified import paths against `nautilus_trader==1.221.0`.
* Ensured **no data leakage** — indicators computed strictly on prior bars.
* Random seed fixed for reproducibility.
* Verified FastAPI and test suite pass under Python **3.13.1**.

---

## 🧭 Improvements (Next Steps)

* Add **FillModel calibration** from historical trade-through rates.
* Introduce **partial fill simulation** and latency offset.
* Migrate partitioned schema to **TimescaleDB hypertables** for production scale.
* Integrate real **Databento adapter** once API access is granted.

---

## 📜 Author

**Shubham Gupta**
M.Sc. in Data Science | B.Tech in Electronics & Communication

---

## 🏁 Final Status

✅ **All four phases (T1–T4) completed successfully**
✅ **All tests passed**
✅ **Documentation + reproducibility verified**

> “A complete, deterministic, and scalable trading evaluation — ready for review.”

---

```