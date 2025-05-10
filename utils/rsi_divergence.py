import pandas as pd
from ta.momentum import RSIIndicator


def detect_rsi_divergence(df: pd.DataFrame, direction: str, lookback: int = 5) -> bool:
    """Обнаруживает RSI-дивергенцию:
    - бычья: цена делает ниже минимум, RSI — нет
    - медвежья: цена делает выше максимум, RSI — нет.

    :param df: OHLCV DataFrame
    :param direction: "long" или "short"
    :param lookback: кол-во свечей для анализа
    :return: True, если дивергенция подтверждена
    """
    if df.shape[0] < lookback + 2:
        return False

    rsi = RSIIndicator(close=df["close"], window=14).rsi()
    close = df["close"]

    if direction == "long":
        recent_low = close.iloc[-1]
        past_low = close.iloc[-lookback-1]
        recent_rsi = rsi.iloc[-1]
        past_rsi = rsi.iloc[-lookback-1]

        return recent_low < past_low and recent_rsi > past_rsi

    if direction == "short":
        recent_high = close.iloc[-1]
        past_high = close.iloc[-lookback-1]
        recent_rsi = rsi.iloc[-1]
        past_rsi = rsi.iloc[-lookback-1]

        return recent_high > past_high and recent_rsi < past_rsi

    return False
