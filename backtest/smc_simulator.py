import asyncio
import random
import pandas as pd

from api.bybit_async import get_ohlcv
from log_setup import logger


async def simulate_smc_on_history(symbol: str, capital=1000, risk_pct=0.01):
    raw = await get_ohlcv(symbol=symbol, interval="1h", limit=1000)
    if not raw:
        logger.warning(f"⛔ Нет данных по {symbol}")
        return {"symbol": symbol, "total": 0, "wins": 0, "avg_rr": None}

    df = pd.DataFrame(raw)
    if df.empty:
        logger.warning(f"⛔ Пустой DataFrame по {symbol}")
        return {"symbol": symbol, "total": 0, "wins": 0, "avg_rr": None}

    wins, losses, rr_list = 0, 0, []

    for i in range(100, len(df)):
        df_slice = df.iloc[:i].copy()
        outcome = simulate_trade(df_slice)
        if outcome:
            rr_list.append(outcome["rr"])
            if outcome["rr"] >= 1:
                wins += 1
            else:
                losses += 1

    total = wins + losses
    avg_rr = round(sum(rr_list) / len(rr_list), 2) if rr_list else 0
    return {
        "symbol": symbol,
        "total": total,
        "wins": wins,
        "avg_rr": avg_rr,
    }


def simulate_trade(df):
    rr = round(random.uniform(0.5, 3.0), 2)
    return {"rr": rr}


if __name__ == "__main__":
    result = asyncio.run(simulate_smc_on_history("BTC/USDT"))
    print(result)
