import pandas as pd
from strategies.smc_strategy import run_smc_strategy
from utils.log_signal import log_signal
import asyncio

async def simulate_on_csv(filepath: str, symbol: str = "BTCUSDT"):
    df = pd.read_csv(filepath)
    df = df.rename(columns=str.lower)
    df = df.rename(columns={"timestamp": "time"})
    df = df.tail(150)  # последние 150 свечей

    for i in range(10):
        current_df = df.tail(150).copy()
        close = current_df["close"].iloc[-1]

        result = await run_smc_strategy(symbol=symbol, capital=1000)
        print(f"📍 Прогон {i+1}: {result}")
        await asyncio.sleep(1)  # искусственная пауза

if __name__ == "__main__":
    asyncio.run(simulate_on_csv("data/historical/BTCUSDT_1h.csv"))
