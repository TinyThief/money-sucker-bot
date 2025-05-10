import json
import os
import random
from datetime import datetime
from typing import Optional

import pandas as pd
import matplotlib.pyplot as plt
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from telegram import Update, InputFile
from telegram.ext import ContextTypes

from utils.confidence_weights import CONFIDENCE_WEIGHTS

SIGNAL_LOG_PATH = "logs/signal_log.csv"
PARAM_GRID = {
    "bos": [20, 30, 40],
    "fvg": [10, 20, 30],
    "rsi_extreme": [10, 20, 30],
    "rsi_bounce": [0, 5, 10],
    "ema_filter": [5, 10, 15],
    "macd": [0, 5, 10],
    "vwap": [5, 10, 15],
    "volume_spike": [5, 10, 15],
    "candle_confirm": [5, 10, 15],
    "bounce_vwap": [5, 10, 15],
    "obv_trend": [0, 5, 10],
    "liq_nearby": [0, 10, 15],
    "htf_match_4h": [5, 10, 15],
    "htf_mismatch_4h": [-10, -5, 0],
    "htf_match_1d": [10, 15, 20],
    "htf_mismatch_1d": [-15, -10, -5],
}

BEST_FILE = "config/best_weights.json"
PLOT_FILE = "logs/confidence_weights_plot.png"
BACKTESTS_DIR = "backtests"

scheduler = AsyncIOScheduler()


def evaluate_weights(weights: dict) -> float:
    if not os.path.exists(SIGNAL_LOG_PATH):
        return 0
    try:
        df = pd.read_csv(SIGNAL_LOG_PATH, header=None)
        df.columns = [
            "timestamp", "symbol", "direction", "entry_price", "sl_price", "tp_price",
            "size", "confidence", "reasons", "status", "result", "pnl"
        ]
        df = df.dropna(subset=["reasons", "result"])
        total, tp = 0, 0
        for _, row in df.iterrows():
            reasons = str(row["reasons"]).split("; ")
            conf = sum(weights.get(r.strip(), 0) for r in reasons)
            if conf >= 50:
                total += 1
                if row["result"] == "tp":
                    tp += 1
        return tp / total if total > 0 else 0
    except:
        return 0


def grid_search(max_tests=100):
    keys = list(PARAM_GRID.keys())
    best_score = 0
    best_weights = CONFIDENCE_WEIGHTS.copy()

    for _ in range(max_tests):
        test_weights = {k: random.choice(PARAM_GRID[k]) for k in keys}
        score = evaluate_weights(test_weights)
        if score > best_score:
            best_score = score
            best_weights = test_weights

    return best_weights, best_score


def save_weights_plot(weights: dict):
    labels = list(weights.keys())
    values = list(weights.values())
    plt.figure(figsize=(12, 6))
    plt.bar(labels, values)
    plt.xticks(rotation=45, ha="right")
    plt.title("Лучшие confident-веса по результатам Grid Search")
    plt.grid(True, axis="y")
    plt.tight_layout()
    os.makedirs("logs", exist_ok=True)
    plt.savefig(PLOT_FILE)
    plt.close()


async def cmd_optimize_confidence(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if update.message:
            formatted = json.dumps(CONFIDENCE_WEIGHTS, indent=2)
            await update.message.reply_text(
                f"🧠 Текущие confident веса:\n<pre>{formatted}</pre>\n\nИзменить можно вручную в config/confidence_weights.json",
                parse_mode="HTML"
            )
    except Exception as e:
        if update.message:
            await update.message.reply_text(f"❌ Ошибка отображения весов: {e}")


async def cmd_optimize_confidence_auto(update: Optional[Update] = None, context: Optional[ContextTypes.DEFAULT_TYPE] = None) -> None:
    try:
        best_weights, best_score = grid_search(max_tests=100)

        os.makedirs("config", exist_ok=True)
        with open(BEST_FILE, "w", encoding="utf-8") as f:
            json.dump({"score": round(best_score, 4), "weights": best_weights}, f, indent=4)

        save_weights_plot(best_weights)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        export_dir = os.path.join(BACKTESTS_DIR, timestamp)
        os.makedirs(export_dir, exist_ok=True)

        with open(os.path.join(export_dir, "best_weights.json"), "w", encoding="utf-8") as f:
            json.dump({"score": round(best_score, 4), "weights": best_weights}, f, indent=4)

        summary_txt = f"Grid Search Summary\nScore: {best_score:.4f}\n\n"
        summary_txt += "\n".join([f"{k}: {v}" for k, v in best_weights.items()])
        with open(os.path.join(export_dir, "summary.txt"), "w", encoding="utf-8") as f:
            f.write(summary_txt)

        if os.path.exists(PLOT_FILE):
            import shutil
            shutil.copy(PLOT_FILE, os.path.join(export_dir, "confidence_weights_plot.png"))

        if update and update.message:
            await update.message.reply_text(
                f"✅ Grid Search завершён!\nЛучший score: {best_score:.3f}\nРезультаты сохранены в: {export_dir}"
            )
            with open(PLOT_FILE, "rb") as img:
                await update.message.reply_photo(InputFile(img), caption="📊 Итоговые confident-веса")
        else:
            print(f"[AUTO] Grid Search завершён — Score: {best_score:.3f} | Сохранено в: {export_dir}")
    except Exception as e:
        if update and update.message:
            await update.message.reply_text(f"❌ Ошибка при grid search: {e}")
        else:
            print(f"[AUTO] Ошибка при grid search: {e}")


# Планировщик запуска в 02:00 каждый день
scheduler.add_job(cmd_optimize_confidence_auto, trigger="cron", hour=2, minute=0)
