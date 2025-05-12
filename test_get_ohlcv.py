import asyncio
import json
from api.bybit_async import get_ohlcv

async def test():
    candles = await get_ohlcv("BTCUSDT", interval="60", limit=10)
    print("📊 OHLCV данные:")
    print(json.dumps(candles, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(test())
