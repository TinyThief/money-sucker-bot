import pandas as pd
from core.trade_planner import TradePlanner
from log_setup import logger
from utils.metrics_logger import log_trade_metrics


def backtest_from_csv(symbol: str, csv_path: str, capital: float = 1000, confidence: float = 65):
    df = pd.read_csv(csv_path)
    if df.empty or len(df) < 100:
        logger.error(f"❌ Недостаточно данных для {symbol}")
        return None

    equity = capital
    trades = []

    for i in range(100, len(df) - 10):
        entry_price = df["close"].iloc[i]
        direction = "long" if i % 2 == 0 else "short"

        planner = TradePlanner(
            balance=equity,
            confidence=confidence,
            entry_price=entry_price,
            direction=direction
        )
        plan = planner.generate()

        sl, tp1, tp2 = plan["sl"], plan["tp1"], plan["tp2"]
        size = plan["size"]
        if size == 0 or not sl or not tp2:
            continue

        window = df.iloc[i:i + 10]
        hit = "none"
        exit_price = None

        for _, row in window.iterrows():
            if direction == "long":
                if row["low"] <= sl:
                    hit = "sl"
                    exit_price = sl
                    break
                if row["high"] >= tp2:
                    hit = "tp"
                    exit_price = tp2
                    break
            else:
                if row["high"] >= sl:
                    hit = "sl"
                    exit_price = sl
                    break
                if row["low"] <= tp2:
                    hit = "tp"
                    exit_price = tp2
                    break

        if hit == "none" or exit_price is None:
            continue

        pnl = (exit_price - entry_price) * size if direction == "long" else (entry_price - exit_price) * size
        equity += pnl

        log_trade_metrics(
            symbol=symbol,
            direction=direction,
            entry=entry_price,
            sl=sl,
            tp=tp2,
            result=hit,
            rr=2.0,
            confidence=confidence,
            pnl=pnl
        )

        trades.append({
            "entry_time": i,
            "direction": direction,
            "entry": entry_price,
            "exit": exit_price,
            "result": hit,
            "size": size,
            "pnl": pnl,
            "equity": equity
        })

    df_trades = pd.DataFrame(trades)
    logger.info(f"\n📊 Результаты по {symbol}:")
    logger.info(f"• Сделок: {len(df_trades)}")
    logger.info(f"• Финальный equity: {round(equity, 2)}")
    logger.info(f"• Прибыль: {round(equity - capital, 2)}")

    return df_trades


if __name__ == "__main__":
    backtest_from_csv("BTCUSDT", "data/historical/BTCUSDT_1h.csv")
