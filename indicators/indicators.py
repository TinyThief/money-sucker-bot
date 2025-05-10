import logging
import pandas as pd
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volume import OnBalanceVolumeIndicator

logger = logging.getLogger("Indicators")
logger.setLevel(logging.INFO)

def get_indicators(df: pd.DataFrame) -> dict:
    required_columns = ["close", "high", "low", "volume", "open"]
    for col in required_columns:
        if col not in df.columns:
            logger.error(f"Отсутствует необходимый столбец: {col}")
            return dict.fromkeys([
                "ema_50", "ema_100", "ema_200",
                "rsi", "macd_hist", "macd_signal", "macd_line", "macd",
                "obv", "vwap", "above_vwap_3", "below_vwap_3", "delta_volume",
            ])

    try:
        ema_50 = float(EMAIndicator(df["close"], window=50).ema_indicator().iloc[-1])
        ema_100 = float(EMAIndicator(df["close"], window=100).ema_indicator().iloc[-1])
        ema_200 = float(EMAIndicator(df["close"], window=200).ema_indicator().iloc[-1])

        rsi = float(RSIIndicator(df["close"]).rsi().iloc[-1])

        macd = MACD(df["close"])
        macd_hist = float(macd.macd_diff().iloc[-1])
        macd_signal = float(macd.macd_signal().iloc[-1])
        macd_line = float(macd.macd().iloc[-1])

        obv = float(OnBalanceVolumeIndicator(df["close"], df["volume"]).on_balance_volume().iloc[-1])

        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        vwap_series = (typical_price * df["volume"]).cumsum() / df["volume"].cumsum()
        vwap_price = float(vwap_series.iloc[-1])

        last_3_closes = df["close"].iloc[-3:]
        last_3_vwaps = vwap_series.iloc[-3:]
        above_vwap = float(all(c > v for c, v in zip(last_3_closes, last_3_vwaps, strict=False)))
        below_vwap = float(all(c < v for c, v in zip(last_3_closes, last_3_vwaps, strict=False)))

        delta_volume = float(((df["close"] - df["open"]) * df["volume"]).iloc[-1])

        return {
            "ema_50": ema_50,
            "ema_100": ema_100,
            "ema_200": ema_200,
            "rsi": rsi,
            "macd_hist": macd_hist,
            "macd_signal": macd_signal,
            "macd_line": macd_line,
            "macd": macd_line,
            "obv": obv,
            "vwap": vwap_price,
            "above_vwap_3": above_vwap,
            "below_vwap_3": below_vwap,
            "delta_volume": delta_volume,
        }

    except Exception as e:
        logger.error(f"Ошибка при расчёте индикаторов: {e}", exc_info=True)
        return dict.fromkeys([
            "ema_50", "ema_100", "ema_200",
            "rsi", "macd_hist", "macd_signal", "macd_line", "macd",
            "obv", "vwap", "above_vwap_3", "below_vwap_3", "delta_volume",
        ])
