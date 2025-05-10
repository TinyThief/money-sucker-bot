import csv
import os
from datetime import datetime

from log_setup import logger

JOURNAL_FILE = "logs/trade_journal.csv"

# 🔧 Проверка, существует ли файл — если нет, создаём с заголовками
if not os.path.exists(JOURNAL_FILE):
    with open(JOURNAL_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "timestamp", "symbol", "side", "size", "entry", "exit", "pnl",
            "exit_reason", "strategy", "confidence",
        ])

# 🧾 Запись сделки в журнал

def log_trade(
    symbol: str,
    side: str,
    size: float,
    entry_price: float,
    exit_price: float,
    pnl: float,
    exit_reason: str,
    strategy: str = "SMC",
    confidence: float = 0.0,
) -> None:
    try:
        with open(JOURNAL_FILE, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                symbol,
                side,
                round(size, 4),
                round(entry_price, 4),
                round(exit_price, 4),
                round(pnl, 4),
                exit_reason,
                strategy,
                round(confidence, 2),
            ])
        logger.info(f"📝 Сделка по {symbol} записана в журнал: {exit_reason}, PnL = {pnl:.2f}")
    except Exception as e:
        logger.error(f"❌ Ошибка при записи в журнал сделок: {e}")
