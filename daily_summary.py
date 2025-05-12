import pandas as pd
import os
import time
from datetime import datetime
import asyncio
import json

from utils.telegram_utils import send_telegram_message, send_telegram_photo
from utils.equity_plot import plot_equity_curve
from backtest.optimize_confidence import grid_search

SIGNAL_LOG_PATH = "logs/signal_log.csv"
SUMMARY_PATH = "logs/daily_summary.csv"


def generate_daily_summary():
    if not os.path.exists(SIGNAL_LOG_PATH):
        print("Нет сигналов для анализа")
        return

    df = pd.read_csv(SIGNAL_LOG_PATH, header=None)
    df.columns = [
        "timestamp", "symbol", "direction", "entry_price", "sl_price", "tp_price",
        "size", "confidence", "reasons", "status", "result", "pnl"
    ]

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce").fillna(0)

    today = datetime.utcnow().date()
    df_today = df[df["timestamp"].dt.date == today]

    if df_today.empty:
        print("Сегодня сделок не было")
        return

    trades = len(df_today)
    wins = (df_today["result"] == "tp").sum()
    losses = (df_today["result"] == "sl").sum()
    total_pnl = df_today["pnl"].sum()
    win_rate = wins / trades if trades else 0

    row = {
        "date": today.isoformat(),
        "trades": trades,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 2),
        "pnl": round(total_pnl, 2)
    }

    # Сохраняем CSV
    df_summary = pd.DataFrame([row])
    if os.path.exists(SUMMARY_PATH):
        df_summary.to_csv(SUMMARY_PATH, mode="a", header=False, index=False)
    else:
        df_summary.to_csv(SUMMARY_PATH, index=False)

    # Telegram: Сводка
    msg = (
        f"📊 <b>Сводка за {today}</b>\n"
        f"• Сделок: {trades}\n"
        f"• Побед: {wins} | Поражений: {losses}\n"
        f"• Win-rate: {win_rate:.2%}\n"
        f"• Общий PnL: {total_pnl:+.2f} USDT"
    )

    try:
        asyncio.run(send_telegram_message(msg, parse_mode="HTML"))
    except Exception as e:
        print("Ошибка отправки Telegram отчёта:", e)

    # Telegram: График equity
    image_path = plot_equity_curve(log_file="logs/signals.jsonl")
    if image_path:
        try:
            asyncio.run(send_telegram_photo(image_path, caption="📈 Equity Curve"))
        except Exception as e:
            print("Ошибка отправки графика Equity:", e)

    # Telegram: Оптимизация confident-весов
    try:
        best_weights, best_score, top_profiles = grid_search(max_tests=100)

        weights_json = {
            "score": round(best_score, 4),
            "weights": best_weights
        }
        with open("config/best_weights.json", "w", encoding="utf-8") as f:
            json.dump(weights_json, f, indent=4)

        # Сохраняем топ-5 профилей
        os.makedirs("config/profiles", exist_ok=True)
        for i, (weights, score) in enumerate(top_profiles):
            with open(f"config/profiles/profile_{i+1}_{int(score*100)}.json", "w", encoding="utf-8") as f:
                json.dump({"score": round(score, 4), "weights": weights}, f, indent=4)

        opt_msg = (
            f"🧠 <b>Confident оптимизация завершена</b>\n"
            f"• Score: <b>{best_score:.3f}</b>\n"
            f"• Веса обновлены в best_weights.json"
        )
        asyncio.run(send_telegram_message(opt_msg, parse_mode="HTML"))
    except Exception as e:
        print("Ошибка оптимизации confident-весов:", e)


if __name__ == "__main__":
    generate_daily_summary()
