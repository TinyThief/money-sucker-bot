
import pandas as pd


def detect_candlestick_patterns(df: pd.DataFrame) -> dict:
    patterns = {
        "bullish_engulfing": False,
        "bearish_engulfing": False,
        "bullish_pin_bar": False,
        "bearish_pin_bar": False,
    }

    if len(df) < 2:
        return patterns

    c1 = df.iloc[-2]
    c2 = df.iloc[-1]

    # Bullish Engulfing
    if c1["close"] < c1["open"] and c2["close"] > c2["open"] and c2["close"] > c1["open"] and c2["open"] < c1["close"]:
        patterns["bullish_engulfing"] = True

    # Bearish Engulfing
    if c1["close"] > c1["open"] and c2["close"] < c2["open"] and c2["open"] > c1["close"] and c2["close"] < c1["open"]:
        patterns["bearish_engulfing"] = True

    # Bullish Pin Bar
    if (c2["low"] < c2["open"]) and (c2["low"] < c2["close"]) and (c2["high"] - max(c2["open"], c2["close"]) < (min(c2["open"], c2["close"]) - c2["low"]) * 0.5):
        patterns["bullish_pin_bar"] = True

    # Bearish Pin Bar
    if (c2["high"] > c2["open"]) and (c2["high"] > c2["close"]) and (min(c2["open"], c2["close"]) - c2["low"] < (c2["high"] - max(c2["open"], c2["close"])) * 0.5):
        patterns["bearish_pin_bar"] = True

    return patterns
