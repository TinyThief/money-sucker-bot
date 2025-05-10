def calculate_sl_tp(entry: float, direction: str, rr: float, sl_pct: float) -> dict | None:
    if entry <= 0 or rr <= 0 or sl_pct <= 0:
        return None

    if direction == "long":
        sl = entry * (1 - sl_pct)
        tp = entry + (entry - sl) * rr
    elif direction == "short":
        sl = entry * (1 + sl_pct)
        tp = entry - (sl - entry) * rr
    else:
        return None

    return {
        "stop_loss": round(sl, 4),
        "take_profit": round(tp, 4),
    }
