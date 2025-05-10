import unittest

import pandas as pd

from indicators.candlestick_patterns import detect_candlestick_patterns


class TestCandlestickPatterns(unittest.TestCase):

    def test_bullish_engulfing(self) -> None:
        df = pd.DataFrame({
            "open": [100, 95],
            "high": [101, 100],
            "low": [94, 90],
            "close": [95, 98],
        })
        patterns = detect_candlestick_patterns(df)
        assert "bullish_engulfing" in patterns

    def test_bearish_engulfing(self) -> None:
        df = pd.DataFrame({
            "open": [100, 105],
            "high": [101, 106],
            "low": [99, 100],
            "close": [105, 100],
        })
        patterns = detect_candlestick_patterns(df)
        assert "bearish_engulfing" in patterns

if __name__ == "__main__":
    unittest.main()
