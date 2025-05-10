import asyncio

from strategies.smc_strategy import run_smc_strategy

if __name__ == "__main__":
    symbols = [
        "BTCUSDT", "ETHUSDT", "XRPUSDT", "EOSUSDT",
        "ADAUSDT", "BNBUSDT", "SOLUSDT", "ATOMUSDT",
    ]

    async def main() -> None:
        for symbol in symbols:
            print(f"\n🚀 Запуск стратегии для {symbol}...")
            await run_smc_strategy(symbol, capital=1000)

    asyncio.run(main())
