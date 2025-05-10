
import asyncio
import json
from api.bybit_async import get_exchange, get_ohlcv
from strategies.smc_strategy import run_smc_strategy
from log_setup import logger

async def fetch_bybit_symbols():
    ex = await get_exchange()
    markets = await ex.load_markets()
    return [
        symbol for symbol in markets
        if symbol.endswith("USDT") and ":USDT" not in symbol and markets[symbol]["active"]
    ]

async def filter_top_symbols(symbols, top_n=10):
    scored = []
    for symbol in symbols:
        try:
            df = await get_ohlcv(symbol, interval="1h", limit=50)
            if df:
                closes = [c["close"] for c in df]
                volumes = [c["volume"] for c in df]
                volatility = max(closes) / min(closes) - 1
                total_volume = sum(volumes)
                score = volatility * total_volume
                scored.append((symbol, score))
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при анализе {symbol}: {e}")
            continue
    scored.sort(key=lambda x: x[1], reverse=True)
    return [s[0] for s in scored[:top_n]]

CAPITAL = 1000

async def main():
    logger.info("📊 Получение списка всех активных пар...")
    symbols = await fetch_bybit_symbols()
    logger.info(f"🔎 Найдено {len(symbols)} пар. Оцениваем...")
    top_symbols = await filter_top_symbols(symbols, top_n=10)
    logger.info(f"✅ Топ-пары выбраны: {top_symbols}")

    tasks = []
    for symbol in top_symbols:
        tasks.append(run_smc_strategy(symbol, capital=CAPITAL))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
