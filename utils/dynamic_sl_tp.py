import pandas as pd
import json
import os

SL_TP_WEIGHTS_PATH = "config/sl_tp_weights.json"

try:
    with open(SL_TP_WEIGHTS_PATH, "r", encoding="utf-8") as f:
        SL_TP_WEIGHTS = json.load(f)
except FileNotFoundError:
    SL_TP_WEIGHTS = {}

def calculate_manual_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return true_range.rolling(window=period, min_periods=1).mean()

def bucket_confidence(conf: float) -> str:
    if conf < 0.4:
        return "low_confidence"
    elif conf < 0.7:
        return "mid_confidence"
    else:
        return "high_confidence"

def get_dynamic_sl_tp_advanced(df: pd.DataFrame, entry: float, direction: str, confidence: float, symbol: str = "BTCUSDT") -> dict:
    atr = calculate_manual_atr(df)
    current_atr = atr.iloc[-1] if not atr.empty else entry * 0.01

    group = bucket_confidence(confidence)
    weights = SL_TP_WEIGHTS.get(symbol, {}).get(group, {})

    sl_buffer = weights.get("sl_buffer", 1.0)
    tp_rr = weights.get("tp_rr", 2.0)

    sl_distance = current_atr * sl_buffer
    tp_distance = sl_distance * tp_rr

    if direction == "long":
        sl = entry - sl_distance
        tp = entry + tp_distance
    else:
        sl = entry + sl_distance
        tp = entry - tp_distance

    return {
        "sl": round(sl, 2),
        "tp1": None,
        "tp2": round(tp, 2),
        "tp1_ratio": 0.0,
        "tp2_ratio": 1.0
    }
def save_sl_tp_weights(weights: dict) -> None:
    with open(SL_TP_WEIGHTS_PATH, "w", encoding="utf-8") as f:
        json.dump(weights, f, indent=2, ensure_ascii=False)
    print(f"✅ Конфигурация SL/TP сохранена в {SL_TP_WEIGHTS_PATH}")