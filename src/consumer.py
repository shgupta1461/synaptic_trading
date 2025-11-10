import asyncio
import pandas as pd
from collections import deque, defaultdict
from stream_stub import fill_queue, Tick


class PriceConsumer:
    """Consumes async price ticks from stream_stub."""
    def __init__(self, window=200):
        self.buffer = defaultdict(lambda: deque(maxlen=window))
        self.queue = asyncio.Queue()

    async def start(self, symbols=("XYZ",)):
        """Start async listener and processing tasks."""
        asyncio.create_task(fill_queue(self.queue, symbols=symbols))
        asyncio.create_task(self.consume())

    async def consume(self):
        """Consume ticks and update rolling buffer."""
        while True:
            tick: Tick = await self.queue.get()
            self.buffer[tick.symbol].append(tick.price)

    def get_prices(self, symbol: str) -> pd.Series:
        """Return latest price series for symbol."""
        if symbol not in self.buffer or not self.buffer[symbol]:
            return pd.Series(dtype=float)
        return pd.Series(list(self.buffer[symbol]))
