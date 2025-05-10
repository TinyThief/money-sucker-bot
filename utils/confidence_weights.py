import json
import os

CONFIG_PATH = os.path.join("config", "best_weights.json")

DEFAULT_WEIGHTS = {
    "bos": 40,
    "fvg": 20,
    "rsi_extreme": 12,
    "rsi_bounce": 10,
    "ema_filter": 10,
    "macd": 8,
    "vwap": 15,
    "volume_spike": 15,
    "candle_confirm": 8,
    "bounce_vwap": 8,
    "obv_trend": 6,
    "liq_nearby": 10,
    "htf_match_4h": 10,
    "htf_mismatch_4h": -3,
    "htf_match_1d": 20,
    "htf_mismatch_1d": -5,
}

try:
    with open(CONFIG_PATH) as f:
        CONFIDENCE_WEIGHTS = json.load(f)
except Exception:
    CONFIDENCE_WEIGHTS = DEFAULT_WEIGHTS
