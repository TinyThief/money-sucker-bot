from api.bybit_async import get_ohlcv
import asyncio

async def test_fetch():
    data = await get_ohlcv("BTCUSDT", interval="1h", limit=5)
    print("Данные OHLCV:", data)

if __name__ == "__main__":
    asyncio.run(test_fetch())
    