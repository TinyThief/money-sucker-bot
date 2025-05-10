import pandas as pd


def check_volume_spike(df: pd.DataFrame, threshold: float = 1.8) -> bool:
    last_volume = df["volume"].iloc[-1]
    avg_volume = df["volume"].iloc[-30:-1].mean()
    return last_volume > avg_volume * threshold
