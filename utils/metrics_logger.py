import csv
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

METRICS_LOG_PATH = Path("logs/metrics.csv")

# Заголовки CSV-файла
HEADERS = [
    "timestamp", "symbol", "direction", "entry", "sl", "tp",
    "result", "rr", "confidence", "pnl",
]


def log_trade_metrics(
    symbol: str,
    direction: Literal["long", "short"],
    entry: float,
    sl: float,
    tp: float,
    result: str,
    rr: float,
    confidence: float,
    pnl: float | None,
) -> None:
    """Логирует торговую метрику (одна сделка) в metrics.csv."""
    METRICS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    file_exists = METRICS_LOG_PATH.exists()

    with METRICS_LOG_PATH.open(mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "symbol": symbol,
            "direction": direction,
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "result": result,
            "rr": rr,
            "confidence": confidence,
            "pnl": pnl or "",
        })
