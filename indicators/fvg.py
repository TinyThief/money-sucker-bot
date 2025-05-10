
import pandas as pd


def detect_fvg(df: pd.DataFrame) -> list:
    fvg_zones = []

    for i in range(2, len(df)):
        high1 = df.iloc[i-2]["high"]
        low2 = df.iloc[i-1]["low"]

        if low2 > high1:
            fvg_zones.append({
                "start": high1,
                "end": low2,
                "status": "unfilled",
                "index": i,
            })

    return fvg_zones
