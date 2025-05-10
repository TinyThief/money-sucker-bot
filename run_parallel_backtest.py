import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

from backtest.smc_dry_backtest import backtest_smc_dry

# Загрузка пар
with open("config/pairs.json", encoding="utf-8") as f:
    pairs = json.load(f)["pairs"]

results = []

print("🚀 Запуск параллельного backtest...")

def run(symbol):
    try:
        df = backtest_smc_dry(symbol, capital=1000)
        if df is not None:
            profit = df["pnl"].sum()
            winrate = (df["result"] == "tp").mean()
            return {
                "symbol": symbol,
                "trades": len(df),
                "profit": round(profit, 2),
                "winrate": round(winrate * 100, 2),
            }
    except Exception as e:
        return {"symbol": symbol, "error": str(e)}

    return {"symbol": symbol, "trades": 0}

with ThreadPoolExecutor(max_workers=min(8, len(pairs))) as executor:
    futures = {executor.submit(run, symbol): symbol for symbol in pairs}

    for fut in as_completed(futures):
        result = fut.result()
        results.append(result)
        if "error" in result:
            print(f"❌ {result['symbol']}: {result['error']}")
        else:
            print(f"✅ {result['symbol']}: {result['trades']} сделок | Прибыль: {result['profit']} | Winrate: {result['winrate']}%")

# Сводка
total_profit = sum(r.get("profit", 0) for r in results if "error" not in r)
total_trades = sum(r.get("trades", 0) for r in results if "error" not in r)

print("\n📊 Общий итог:")
print(f"• Всего пар: {len(pairs)}")
print(f"• Сделок: {total_trades}")
print(f"• Суммарная прибыль: {round(total_profit, 2)} USDT")

# ✅ Экспорт отчёта в CSV
report_df = pd.DataFrame(results)
report_path = "logs/backtest_summary.csv"
os.makedirs("logs", exist_ok=True)
report_df.to_csv(report_path, index=False, encoding="utf-8")
print(f"\n📁 Отчёт сохранён: {report_path}")
