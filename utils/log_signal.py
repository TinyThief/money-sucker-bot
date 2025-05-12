import os
import csv
from database.db import save_signal
from log_setup import logger
from datetime import datetime, UTC

CSV_PATH = "logs/signal_log.csv"

def append_csv_log(data: dict):
    header = list(data.keys())
    file_exists = os.path.isfile(CSV_PATH)
    with open(CSV_PATH, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

def log_signal(
    symbol: str,
    direction: str,
    price: float,
    sl: float,
    tp: float,
    size: float,
    confidence: float,
    reasons: list[str],
    status: str = "no_trade",
    result: str = "pending",
    pnl: float = 0.0,
) -> None:
    """Сохраняет сигнал в SQLite базу данных и логирует в CSV."""
    try:
        save_signal(
            symbol=symbol,
            direction=direction,
            price=price,
            sl=sl,
            tp=tp,
            size=size,
            confidence=confidence,
            reasons="; ".join(reasons),
            status=status,
            result=result,
            pnl=pnl,
            timestamp=datetime.now(tz=UTC)
        )
        logger.info(
            "📘 Сигнал записан в БД | %s | %s @ %.2f | SL: %.2f | TP: %.2f | Size: %.2f | Conf: %.2f | Status: %s | Result: %s | PnL: %.2f",
            symbol, direction.upper(), price, sl, tp, size, confidence, status, result, pnl,
        )

        append_csv_log({
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "symbol": symbol,
            "direction": direction,
            "price": price,
            "sl": sl,
            "tp": tp,
            "size": size,
            "confidence": confidence,
            "reasons": "; ".join(reasons),
            "status": status,
            "result": result,
            "pnl": pnl,
        })

    except Exception as e:
        logger.error("❌ Ошибка записи сигнала: %s", str(e))
