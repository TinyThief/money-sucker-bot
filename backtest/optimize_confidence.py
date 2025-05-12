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
            reasons_raw = row["reasons"]
            try:
                reasons = str(reasons_raw).split(";")
                conf = sum(weights.get(r.strip(), 0) for r in reasons if isinstance(r, str))
            except Exception as e:
                print(f"⚠️ Ошибка в reasons: {reasons_raw} — {e}")
                conf = 0

            if conf >= 50:
                total += 1
                if row["result"] == "tp":
                    tp += 1

        return tp / total if total > 0 else 0

    except Exception as e:
        print(f"❌ Ошибка в evaluate_weights: {e}")
        return 0


def grid_search(max_tests=100):
    keys = list(PARAM_GRID.keys())
    best_score = 0

    if isinstance(CONFIDENCE_WEIGHTS, dict) and "weights" in CONFIDENCE_WEIGHTS:
        best_weights = CONFIDENCE_WEIGHTS["weights"].copy()
    else:
        best_weights = CONFIDENCE_WEIGHTS.copy()

    all_tested = []

    for _ in range(max_tests):
        test_weights = {k: random.choice(PARAM_GRID[k]) for k in keys}
        score = evaluate_weights(test_weights)
        all_tested.append((test_weights, score))
        if score > best_score:
            best_score = score
            best_weights = test_weights

    if isinstance(best_weights, dict) and "weights" in best_weights:
        best_weights = best_weights["weights"]

    top_profiles = sorted(all_tested, key=lambda x: x[1], reverse=True)[:5]
    return best_weights, best_score, top_profiles


def save_weights_plot(weights: dict):
    if not isinstance(weights, dict):
        print("❌ Ошибка: weights не является словарём")
        return
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
            await update.message.reply_text("🧠 Начинаю оптимизацию confidence-весов...")

        await cmd_optimize_confidence_auto(update, context)

    except Exception as e:
        if update.message:
            await update.message.reply_text(f"❌ Ошибка в /optimize_confidence:\n{e}")


async def cmd_optimize_confidence_auto(update: Optional[Update] = None, context: Optional[ContextTypes.DEFAULT_TYPE] = None) -> None:
    try:
        best_weights, best_score, top_profiles = grid_search(max_tests=100)

        if isinstance(best_weights, dict) and "weights" in best_weights:
            weights_clean = best_weights["weights"]
        else:
            weights_clean = best_weights if isinstance(best_weights, dict) else {}

        os.makedirs("config", exist_ok=True)
        with open(BEST_FILE, "w", encoding="utf-8") as f:
            json.dump({"score": round(best_score, 4), "weights": weights_clean}, f, indent=4)

        os.makedirs("config/profiles", exist_ok=True)
        for i, (weights, score) in enumerate(top_profiles):
            with open(f"config/profiles/profile_{i+1}_{int(score*100)}.json", "w", encoding="utf-8") as f:
                json.dump({"score": round(score, 4), "weights": weights}, f, indent=4)

        # Очистка старых
        import glob
        MAX_PROFILES = 10
        profile_files = sorted(
            glob.glob("config/profiles/profile_*.json"),
            key=os.path.getmtime,
            reverse=True
        )
        for old_file in profile_files[MAX_PROFILES:]:
            try:
                os.remove(old_file)
            except Exception as e:
                print(f"Не удалось удалить старый профиль {old_file}: {e}")

        if isinstance(weights_clean, dict):
            save_weights_plot(weights_clean)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        export_dir = os.path.join(BACKTESTS_DIR, timestamp)
        os.makedirs(export_dir, exist_ok=True)

        with open(os.path.join(export_dir, "best_weights.json"), "w", encoding="utf-8") as f:
            json.dump({"score": round(best_score, 4), "weights": weights_clean}, f, indent=4)

        summary_txt = f"Grid Search Summary\nScore: {best_score:.4f}\n\n"
        if isinstance(weights_clean, dict):
            summary_txt += "\n".join([f"{k}: {v}" for k, v in weights_clean.items()])
        else:
            summary_txt += "\n⚠️ Неверный формат весов"

        with open(os.path.join(export_dir, "summary.txt"), "w", encoding="utf-8") as f:
            f.write(summary_txt)

        if os.path.exists(PLOT_FILE):
            import shutil
            shutil.copy(PLOT_FILE, os.path.join(export_dir, "confidence_weights_plot.png"))

        if update and update.message:
            await update.message.reply_text(
                f"✅ Grid Search завершён!\nЛучший score: {best_score:.3f}\nТоп-5 профилей сохранены в config/profiles/"
            )
            with open(PLOT_FILE, "rb") as img:
                await update.message.reply_photo(InputFile(img), caption="📊 Итоговые confident-веса")
        else:
            print(f"[AUTO] Grid Search завершён — Score: {best_score:.3f}")

    except Exception as e:
        if update and update.message:
            await update.message.reply_text(f"❌ Ошибка при grid search: {e}")
        else:
            print(f"[AUTO] Ошибка при grid search: {e}")


# Планировщик запуска в 02:00 каждый день
scheduler.add_job(cmd_optimize_confidence_auto, trigger="cron", hour=2, minute=0)
