import csv
import os
from datetime import datetime

from log_setup import logger

# Путь к CSV-файлу для записи логов решений
LOG_FILE = "logs/decision_log.csv"

def log_event(symbol: str, step: str, message: str, level: str = "info") -> None:
    """Универсальное логирование решений стратегии:
    - в основной лог (logger)
    - в CSV-файл (decision_log.csv).

    :param symbol: торговая пара (например, "BTC/USDT")
    :param step: этап логики (например: "entry", "risk", "signal", "sl_tp", "reject")
    :param message: текст сообщения
    :param level: уровень логирования: info, warning, error
    """
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    tag = f"[{symbol}][{step.upper()}]"

    # Лог в stdout и файл
    if level == "info":
        logger.info(f"{tag} {message}")
    elif level == "warning":
        logger.warning(f"{tag} {message}")
    elif level == "error":
        logger.error(f"{tag} {message}")
    else:
        logger.info(f"{tag} {message}")

    # Лог в CSV
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, symbol, step, level, message])
    except Exception as e:
        logger.error(f"[{symbol}][LOG_WRITE] ❌ Ошибка при записи decision_log.csv: {e}")
