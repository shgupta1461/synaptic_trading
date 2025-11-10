from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import asyncio
import pandas as pd
from src.consumer import PriceConsumer
from src.indicators import moving_average, compute_rsi, trading_decision

app = FastAPI(title="Synaptic Trading Signal Service")

consumer = PriceConsumer()

@app.on_event("startup")
async def startup_event():
    """Start background consumer and preload data from ohlcv.csv."""
    asyncio.create_task(consumer.start(symbols=("XYZ",)))
    try:
        df = pd.read_csv("data/ohlcv.csv")
        df["close"].fillna(method="ffill", inplace=True)
        consumer.buffer["XYZ"].extend(df["close"].tolist()[-200:])
    except Exception as e:
        print(f"Warning: Failed to preload data: {e}")


@app.get("/signal")
async def get_signal(symbol: str = Query(...)):
    prices = consumer.get_prices(symbol)
    if prices.empty:
        return JSONResponse(status_code=404, content={"error": "No data for symbol"})

    ma20 = moving_average(prices, 20)
    ma50 = moving_average(prices, 50)
    rsi = compute_rsi(prices)
    decision = trading_decision(ma20, ma50, rsi)
    trend = "UP" if ma20 > ma50 else "DOWN" if ma20 < ma50 else "FLAT"

    return {
        "symbol": symbol,
        "trend": trend,
        "rsi": rsi,
        "decision": decision
    }


@app.websocket("/ws/signal")
async def websocket_signal(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            for symbol in consumer.buffer.keys():
                prices = consumer.get_prices(symbol)
                if prices.empty:
                    continue
                ma20 = moving_average(prices, 20)
                ma50 = moving_average(prices, 50)
                rsi = compute_rsi(prices)
                decision = trading_decision(ma20, ma50, rsi)
                await ws.send_json({
                    "symbol": symbol,
                    "trend": "UP" if ma20 > ma50 else "DOWN" if ma20 < ma50 else "FLAT",
                    "rsi": rsi,
                    "decision": decision
                })
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        pass
