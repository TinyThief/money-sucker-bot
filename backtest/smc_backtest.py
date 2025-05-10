import asyncio
import pandas as pd

from api.bybit_async import get_ohlcv
from indicators.eqh_eql import find_equal_highs_lows
from indicators.fvg import detect_fvg
from indicators.indicators import get_indicators
from indicators.market_structure import detect_market_structure
from position_manager.manager import calculate_sl_tp
from utils.direction import determine_direction
from utils.safe_tools import safe_execute
from core.trade_planner import TradePlanner
from utils.log_signal import log_signal


async def simulate_smc_on_history(symbol: str, timeframe: str = "1h", capital: float = 1000, risk_pct: float = 0.01):
    raw = await get_ohlcv(symbol=symbol, interval=timeframe, limit=500)
    if not raw or not isinstance(raw, list):
        print(f"⚠️ Нет данных по {symbol}")
        return None

    df = pd.DataFrame(raw)
    if df.empty:
        print(f"⚠️ Нет данных по {symbol}")
        return None

    trades = []
    for i in range(50, len(df)):
        sliced = df.iloc[:i].copy()
        ms = detect_market_structure(sliced)
        detect_fvg(sliced)
        eq = find_equal_highs_lows(sliced)
        get_indicators(sliced)

        if not ms or ms["trend"] == "neutral":
            continue

        direction = determine_direction(ms["trend"], eq["liquidity_scenario"])
        if direction == "neutral":
            continue

        entry_price = sliced["close"].iloc[-1]
        sl_tp = await safe_execute(calculate_sl_tp, entry=entry_price, direction=direction)
        if not sl_tp:
            continue

        rr = abs(sl_tp["take_profit"] - entry_price) / abs(sl_tp["stop_loss"] - entry_price)
        trade = {
            "entry_time": sliced.index[-1] if isinstance(sliced.index, pd.DatetimeIndex) else i,
            "direction": direction,
            "entry": entry_price,
            "sl": sl_tp["stop_loss"],
            "tp": sl_tp["take_profit"],
            "rr": round(rr, 2),
        }
        trades.append(trade)

    df_trades = pd.DataFrame(trades)
    if df_trades.empty:
        print(f"❌ Сделок не найдено по {symbol}")
        return None

    df_trades["result"] = df_trades["rr"].apply(lambda r: 1 if r > 1.5 else 0)
    win_rate = df_trades["result"].mean()
    avg_rr = df_trades["rr"].mean()

    print(f"\n📊 Результаты по {symbol}:")
    print(f"• Сделок: {len(df_trades)}")
    print(f"• Win-rate: {win_rate:.2%}")
    print(f"• Средний RR: {avg_rr:.2f}")

    return df_trades


def run_backtest_on_df(symbol, df, confidence=65.0, log_signals=False, use_weights=None):
    results = []
    equity = 1000

    for i in range(100, len(df) - 10):
        entry = df["close"].iloc[i]
        direction = "long" if i % 2 == 0 else "short"

        planner = TradePlanner(equity, confidence, entry, direction)
        plan = planner.generate()

        sl, tp = plan["sl"], plan["tp2"]
        size = plan["size"]
        if size == 0: continue

        exit_price, result = None, None
        window = df.iloc[i:i+10]
        for _, row in window.iterrows():
            if direction == "long":
                if row["low"] <= sl:
                    exit_price = sl; result = "sl"; break
                if row["high"] >= tp:
                    exit_price = tp; result = "tp"; break
            else:
                if row["high"] >= sl:
                    exit_price = sl; result = "sl"; break
                if row["low"] <= tp:
                    exit_price = tp; result = "tp"; break

        if exit_price:
            pnl = (exit_price - entry) * size if direction == "long" else (entry - exit_price) * size
            equity += pnl
            if log_signals:
                log_signal(symbol, direction, entry, sl, tp, size, confidence, ["BOS"], "dry_run", result or "unknown", pnl)

            results.append({
                "entry": entry, "exit": exit_price, "pnl": pnl, "equity": equity, "result": result
            })

    return pd.DataFrame(results)


if __name__ == "__main__":
    asyncio.run(simulate_smc_on_history("BTC/USDT"))
