import json

from backtest.smc_simulator import simulate_smc_on_history

# Загружаем пары
with open("config/pairs.json") as f:
    pairs = json.load(f)["pairs"]

results = []
for symbol in pairs:
    print(f"🔁 Тестируем {symbol}...")
    res = simulate_smc_on_history(symbol, capital=1000, risk_pct=0.01)
    results.append(res)

# Вывод общей статистики
total_trades = sum(r["total"] for r in results)
total_wins = sum(r["wins"] for r in results)
avg_rr = round(sum(r["avg_rr"] for r in results if r["avg_rr"]) / len(results), 2)

print("\n📊 Обзор бэктеста:")
print(f"→ Всего сделок: {total_trades}")
print(f"→ Winrate: {round(total_wins / total_trades * 100, 2)}%")
print(f"→ Средний RR: {avg_rr}")
