
import pandas as pd


def detect_market_structure(df: pd.DataFrame) -> dict:
    structure = {
        "trend": "consolidation",
        "event": None,
        "highs": [],
        "lows": [],
    }

    df["swing_high"] = df["high"][(df["high"] > df["high"].shift(1)) & (df["high"] > df["high"].shift(-1))]
    df["swing_low"] = df["low"][(df["low"] < df["low"].shift(1)) & (df["low"] < df["low"].shift(-1))]

    highs = df["swing_high"].dropna()
    lows = df["swing_low"].dropna()

    if len(highs) > 1 and highs.iloc[-1] > highs.iloc[-2]:
        structure["event"] = "BOS"
        structure["trend"] = "bullish"
    elif len(lows) > 1 and lows.iloc[-1] < lows.iloc[-2]:
        structure["event"] = "CHoCH"
        structure["trend"] = "bearish"
    else:
        structure["trend"] = "consolidation"

    structure["highs"] = highs
    structure["lows"] = lows

    return structure
