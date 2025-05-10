import os
import sys
import asyncio
import pandas as pd
from datetime import datetime, timedelta
import ccxt.async_support as ccxt

# Настройка путей
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Параметры
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

TIMEFRAMES = ["1m", "15m", "1h", "4h", "1d"]
LIMIT = 1000  # максимальный размер выборки
import os

EXCHANGE = ccxt.binance({
    "enableRateLimit": True,
    "options": {"defaultType": "future"}
})

async def fetch_ohlcv(symbol: str, timeframe: str, since: int):
    try:
        ohlcv = await EXCHANGE.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=LIMIT)
        return ohlcv
    except Exception as e:
        print(f"[ERROR] fetch_ohlcv({symbol}, {timeframe}) — {e}")
        return []

async def fetch_orderbook(symbol: str):
    try:
        ob = await EXCHANGE.fetch_order_book(symbol)
        ts = int(datetime.utcnow().timestamp() * 1000)
        return {"timestamp": ts, "symbol": symbol, "bids": ob["bids"], "asks": ob["asks"]}
    except Exception as e:
        print(f"[ERROR] fetch_orderbook({symbol}) — {e}")
        return {}

async def download_ohlcv(symbol: str, timeframe: str, days: int = 730):
    print(f"⬇️ OHLCV: {symbol} ({timeframe})")
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    since = int(start.timestamp() * 1000)

    all_data = []
    while since < int(end.timestamp() * 1000):
        batch = await fetch_ohlcv(symbol, timeframe, since)
        if not batch or len(batch) < LIMIT:
            break
        all_data.extend(batch)
        since = batch[-1][0] + 1
        await asyncio.sleep(EXCHANGE.rateLimit / 1000)

    if all_data:
        df = pd.DataFrame(all_data, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        path = f"data/historical/{symbol.replace('/', '')}_{timeframe}.csv"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        df.to_csv(path, index=False)
        print(f"✅ Saved: {path}")
    else:
        print(f"⚠️ Нет данных для {symbol} ({timeframe})")
    return all_data

async def download_orderbook_snapshot(symbol: str):
    print(f"📥 OrderBook snapshot: {symbol}")
    ob = await fetch_orderbook(symbol)
    if ob:
        ts = datetime.utcfromtimestamp(ob["timestamp"] / 1000).strftime("%Y-%m-%d %H:%M:%S")
        path = f"data/orderbook/{symbol.replace('/', '')}_snapshot_{ts.replace(':', '-')}.json"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        pd.Series(ob).to_json(path)
        print(f"✅ Saved: {path}")

async def main():
    for symbol in SYMBOLS:
        for tf in TIMEFRAMES:
            await download_ohlcv(symbol, tf, days=730)
        await download_orderbook_snapshot(symbol)

    await EXCHANGE.close()

if __name__ == "__main__":
    asyncio.run(main())
    