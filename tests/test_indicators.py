import unittest

import numpy as np
import pandas as pd

from indicators.indicators import get_indicators


class TestIndicators(unittest.TestCase):
    def setUp(self) -> None:
        # Создаём искусственный датафрейм с OHLCV
        data = {
            "open": np.linspace(100, 110, 100),
            "high": np.linspace(101, 111, 100),
            "low": np.linspace(99, 109, 100),
            "close": np.linspace(100, 110, 100),
            "volume": np.random.randint(1000, 2000, 100),
        }
        self.df = pd.DataFrame(data)

    def test_indicators_keys_exist(self) -> None:
        result = get_indicators(self.df)
        expected_keys = [
            "rsi", "ema_50", "ema_200", "vwap", "macd", "macd_signal", "macd_hist", "obv",
        ]
        for key in expected_keys:
            assert key in result

    def test_values_are_floats(self) -> None:
        result = get_indicators(self.df)
        for val in result.values():
            assert isinstance(val, float)

if __name__ == "__main__":
    unittest.main()
