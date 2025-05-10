import unittest
from pathlib import Path

import pandas as pd

from utils.log_signal import log_signal

SIGNAL_LOG_PATH = Path("logs/signal_log.csv")

HEADERS = [
    "timestamp", "symbol", "direction", "price", "sl", "tp",
    "size", "confidence", "reasons", "status", "result", "pnl",
]


class TestLogSignal(unittest.TestCase):
    def setUp(self) -> None:
        SIGNAL_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        if SIGNAL_LOG_PATH.exists():
            SIGNAL_LOG_PATH.unlink()

    def test_log_signal_creates_and_appends(self) -> None:
        signal_data = {
            "symbol": "BTCUSDT",
            "direction": "long",
            "price": 10000,
            "sl": 9900,
            "tp": 10500,
            "size": 0.1,
            "confidence": 70,
            "reasons": ["BOS", "FVG"],
            "status": "dry_run",
        }

        log_signal(**signal_data)

        assert SIGNAL_LOG_PATH.exists()

        # Указываем заголовки вручную
        df = pd.read_csv(SIGNAL_LOG_PATH, names=HEADERS)
        assert len(df) == 1
        assert "BTCUSDT" in df["symbol"].values
        assert "long" in df["direction"].values


if __name__ == "__main__":
    unittest.main()
