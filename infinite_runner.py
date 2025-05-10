import time
from datetime import datetime

from strategies.smc_strategy import run_smc_strategy

symbols = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT",
    "ADA/USDT", "BNB/USDT", "ATOM/USDT", "EOS/USDT",
]

CAPITAL = 1000
RISK_PCT = 0.01
INTERVAL_MINUTES = 1

print("\n🔄 Бесконечный сканер запущен. Нажмите Ctrl+C для остановки.\n")

import asyncio

async def main():
    print("\n🔄 Бесконечный сканер запущен. Нажмите Ctrl+C для остановки.\n")
    try:
        while True:
            print(f"\n🕒 Цикл запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            for symbol in symbols:
                try:
                    await run_smc_strategy(symbol=symbol, capital=CAPITAL)
                except Exception as e:
                    print(f"❌ Ошибка при обработке {symbol}: {e}")
            print(f"\n⏳ Ожидание {INTERVAL_MINUTES} минут до следующего запуска...\n")
            await asyncio.sleep(INTERVAL_MINUTES * 60)
    except KeyboardInterrupt:
        print("\n🛑 Сканирование остановлено пользователем.")

if __name__ == "__main__":
    asyncio.run(main())
