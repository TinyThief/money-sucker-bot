import json
import os
from datetime import datetime, timedelta

import pandas as pd

from log_setup import logger
from utils.telegram_utils import send_telegram_message

# Путь к журналу сделок
TRADE_JOURNAL_PATH = "logs/trade_journal.csv"
# Путь куда сохранить новые веса
NEW_WEIGHTS_PATH = "config/new_best_weights.json"
# Путь для логов анализа
PERFORMANCE_LOG_PATH = "logs/performance_log.txt"

# Какие причины анализируем
FEATURES = ["bos", "fvg", "liquidity", "rsi_extreme", "macd_trend", "vwap_position", "liquidations"]

def analyze_trades(lookback_days=1):
    if not os.path.exists(TRADE_JOURNAL_PATH):
        logger.warning("⚠️ Файл trade_journal.csv не найден.")
        return {}

    df = pd.read_csv(TRADE_JOURNAL_PATH)

    expected_columns = {"timestamp", "pnl", "reasons"}
    missing = expected_columns - set(df.columns)
    if missing:
        logger.error(f"❌ Отсутствуют нужные колонки в trade_journal.csv: {missing}")
        return {}

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    cutoff = datetime.now() - timedelta(days=lookback_days)
    df = df[df["timestamp"] >= cutoff]

    if df.empty:
        logger.warning("⚠️ Нет сделок для анализа за последние сутки.")
        return {}

    stats = {}

    for feature in FEATURES:
        feature_trades = df[df["reasons"].str.contains(feature, na=False, case=False)]

        if len(feature_trades) == 0:
            continue

        win_trades = feature_trades[feature_trades["pnl"] > 0]
        winrate = len(win_trades) / len(feature_trades)

        stats[feature] = {
            "total_trades": len(feature_trades),
            "winrate": round(winrate * 100, 2),
        }

    return stats

def adjust_confidence_weights(stats, base_weights, threshold=55):
    new_weights = {}

    for feature, weight in base_weights.items():
        winrate = stats.get(feature, {}).get("winrate", None)

        if winrate is None:
            new_weights[feature] = weight
            continue

        if winrate >= threshold:
            new_weights[feature] = round(weight * 1.1, 2)
        else:
            new_weights[feature] = round(weight * 0.9, 2)

    return new_weights

def save_new_weights(weights) -> None:
    with open(NEW_WEIGHTS_PATH, "w") as f:
        json.dump(weights, f, indent=4)
    logger.info("✅ Новые веса сохранены в new_best_weights.json.")

async def send_performance_report(stats) -> None:
    if not stats:
        return

    text = "<b>📊 Автоанализ сделок завершен:</b>\n\n"
    for feature, data in stats.items():
        text += f"• {feature.upper()}: {data['winrate']}% winrate ({data['total_trades']} сделок)\n"

    await send_telegram_message(text)

async def daily_performance_check() -> None:
    try:
        logger.info("🔍 Запуск ежедневного анализа сделок...")

        with open("config/best_weights.json") as f:
            base_weights = json.load(f)

        stats = analyze_trades()

        if not stats:
            return

        new_weights = adjust_confidence_weights(stats, base_weights)

        save_new_weights(new_weights)

        await send_performance_report(stats)

        with open(PERFORMANCE_LOG_PATH, "a") as log_file:
            log_file.write(f"\n--- Анализ от {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            for feature, data in stats.items():
                log_file.write(f"{feature.upper()}: {data['winrate']}% winrate ({data['total_trades']} сделок)\n")

    except Exception as e:
        logger.error(f"❌ Ошибка в daily_performance_check: {e}")
