# utils/equity_plot.py

import json
import os
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd


def plot_equity_curve(log_file: str = "logs/signals.jsonl", save_path: str = "logs/equity_curve.png"):
    if not os.path.exists(log_file):
        print(f"Файл логов не найден: {log_file}")
        return None

    trades = []
    with open(log_file, encoding="utf-8") as f:
        for line in f:
            try:
                trade = json.loads(line)
                if trade.get("status") == "executed":
                    pnl = trade.get("pnl") or 0  # если нет — считаем 0
                    trades.append({
                        "time": trade.get("timestamp") or trade.get("time", datetime.now().isoformat()),
                        "pnl": pnl,
                    })
            except Exception:
                continue  # пропускаем кривые строки

    if not trades:
        print("Нет данных для построения equity.")
        return None

    df = pd.DataFrame(trades)
    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time")
    df["equity"] = df["pnl"].cumsum()

    # Построение графика
    plt.figure(figsize=(10, 5))
    plt.plot(df["time"], df["equity"], label="Equity", color="green")
    plt.title("📊 Equity Curve")
    plt.xlabel("Дата")
    plt.ylabel("P&L")
    plt.grid(True)
    plt.tight_layout()
    plt.legend()
    plt.savefig(save_path)
    plt.close()
    return save_path
