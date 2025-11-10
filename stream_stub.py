# stream_stub.py
# Async price emitter for the evaluation (simulated ticks).
# Usage example:
#   import asyncio
#   from stream_stub import price_stream
#   async def main():
#       async for tick in price_stream(symbols=("XYZ",), interval_ms=50):
#           print(tick)
#   asyncio.run(main())

import asyncio
import random
import time
from dataclasses import dataclass
from typing import AsyncIterator, Iterable, Dict

@dataclass
class Tick:
    symbol: str
    ts: float        # epoch seconds
    price: float

async def price_stream(symbols: Iterable[str] = ("XYZ",),
                       base_price: float = 100.0,
                       jitter: float = 0.08,
                       interval_ms: int = 50) -> AsyncIterator[Tick]:
    """Yield simulated ticks for each symbol at ~interval_ms cadence.
    Prices follow a noisy random walk to emulate micro-movements.
    """
    prices: Dict[str, float] = {s: float(base_price) for s in symbols}
    while True:
        now = time.time()
        for s in symbols:
            drift = random.uniform(-0.02, 0.02)
            shock = random.gauss(0.0, jitter)
            prices[s] = max(0.01, prices[s] * (1.0 + drift*1e-3) + shock)
            yield Tick(symbol=s, ts=now, price=round(prices[s], 6))
        await asyncio.sleep(max(0.0, interval_ms / 1000.0))

async def fill_queue(queue, symbols=("XYZ",), interval_ms=50):
    """Helper: push ticks into an asyncio.Queue for consumers."""
    async for tick in price_stream(symbols=symbols, interval_ms=interval_ms):
        await queue.put(tick)

if __name__ == "__main__":
    async def _demo():
        async for t in price_stream(symbols=("XYZ","ABC"), interval_ms=50):
            print(t)
    asyncio.run(_demo())
