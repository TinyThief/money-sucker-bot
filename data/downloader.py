import os
import sys
import json
import asyncio
import pandas as pd
from datetime import datetime
import aiohttp
import websockets

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

SYMBOLS = ["btcusdt", "ethusdt"]
TIMEFRAMES = ["1m", "15m", "1h", "4h", "1d"]
LIMIT = 1000
BASE_URL = "https://fapi.binance.com"
WS_BASE = "wss://fstream.binance.com"

# Конфиг
MAX_RETRIES = 3
RETRY_DELAY = 1.5
TIMEOUT = aiohttp.ClientTimeout(total=10)

# Универсальный fetch с retry
async def fetch_with_retries(session, url, params, name):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with session.get(url, params=params, timeout=TIMEOUT) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data
                print(f"[{name}] HTTP error {resp.status}")
        except Exception as e:
            print(f"[{name}] Attempt {attempt} failed: {e}")
        if attempt < MAX_RETRIES:
            await asyncio.sleep(RETRY_DELAY * attempt)
    print(f"[{name}] Failed after {MAX_RETRIES} attempts")
    return None

# OHLCV
async def fetch_ohlcv(symbol: str, interval: str):
    url = f"{BASE_URL}/fapi/v1/klines"
    params = {
        "symbol": symbol.upper(),
        "interval": interval,
        "limit": LIMIT
    }
    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
        data = await fetch_with_retries(session, url, params, f"OHLCV {symbol}/{interval}")
        if not data:
            return []
        return data

# Ордербук
async def fetch_orderbook(symbol: str):
    url = f"{BASE_URL}/fapi/v1/depth"
    params = {"symbol": symbol.upper(), "limit": 50}
    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
        data = await fetch_with_retries(session, url, params, f"OrderBook {symbol}")
        if not data:
            return None
        ts = int(datetime.utcnow().timestamp() * 1000)
        return {
            "timestamp": ts,
            "symbol": symbol.upper(),
            "bids": data.get("bids", []),
            "asks": data.get("asks", [])
        }

# Сохраняем OHLCV
async def save_ohlcv(symbol: str, interval: str):
    candles = await fetch_ohlcv(symbol, interval)
    if candles:
        df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume",
                                            "close_time", "quote_asset_volume", "num_trades",
                                            "taker_buy_base_volume", "taker_buy_quote_volume", "ignore"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df = df[["timestamp", "open", "high", "low", "close", "volume"]]
        path = f"data/binance/ohlcv/{symbol.upper()}_{interval}.csv"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        df.to_csv(path, index=False)
        print(f"✅ Saved OHLCV: {path}")

# Сохраняем ордербук
async def save_orderbook_snapshot(symbol: str):
    ob = await fetch_orderbook(symbol)
    if ob:
        ts = datetime.utcfromtimestamp(ob["timestamp"] / 1000).strftime("%Y-%m-%d %H-%M-%S")
        path = f"data/binance/orderbook/{symbol.upper()}_snapshot_{ts}.json"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(ob, f, indent=2)
        print(f"✅ Saved OB: {path}")

# WebSocket ликвидации
async def stream_liquidations(symbol: str):
    url = f"{WS_BASE}/ws/{symbol}@forceOrder"
    async for ws in websockets.connect(url):
        try:
            async for msg in ws:
                data = json.loads(msg)
                ts = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
                path = f"data/binance/liquidations/{symbol.upper()}_wsliq_{ts}.json"
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w") as f:
                    json.dump(data, f, indent=2)
                print(f"📥 WS LIQ: {symbol} @ {ts}")
        except websockets.ConnectionClosed:
            print(f"🔁 Reconnecting to {symbol} WS...")
            continue

# Главный процесс
async def main():
    tasks = []
    for symbol in SYMBOLS:
        for tf in TIMEFRAMES:
            tasks.append(save_ohlcv(symbol, tf))
        tasks.append(save_orderbook_snapshot(symbol))
        tasks.append(stream_liquidations(symbol))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
