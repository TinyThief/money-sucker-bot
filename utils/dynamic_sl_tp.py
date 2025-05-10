def get_dynamic_sl_tp(confidence, entry_price, direction):
    """Returns dynamic SL and TP1/TP2 based on confidence level.
    direction: 'long' or 'short'.
    """
    risk_pct = 1.0
    rr1, rr2 = 1.5, 2.5
    tp1_ratio, tp2_ratio = 0.5, 0.5

    if confidence <= 45:
        risk_pct = 0.5
        rr1, rr2 = 1.2, 2.0
    elif 46 <= confidence <= 60:
        risk_pct = 1.0
        rr1, rr2 = 1.5, 2.5
    elif 61 <= confidence <= 75:
        risk_pct = 1.25
        rr1, rr2 = 1.5, 3.0
        tp1_ratio, tp2_ratio = 0.3, 0.7
    elif confidence > 75:
        risk_pct = 1.5
        rr1 = None  # no TP1
        rr2 = 4.0
        tp1_ratio, tp2_ratio = 0.0, 1.0

    sl_pct = 1.0 / 100
    sl = entry_price * (1 - sl_pct) if direction == "long" else entry_price * (1 + sl_pct)

    tp1 = None
    tp2 = None

    if rr1:
        tp1 = entry_price * (1 + rr1 * sl_pct) if direction == "long" else entry_price * (1 - rr1 * sl_pct)
    if rr2:
        tp2 = entry_price * (1 + rr2 * sl_pct) if direction == "long" else entry_price * (1 - rr2 * sl_pct)

    return {
        "risk_pct": risk_pct,
        "sl": round(sl, 2),
        "tp1": round(tp1, 2) if tp1 else None,
        "tp2": round(tp2, 2) if tp2 else None,
        "tp1_ratio": tp1_ratio,
        "tp2_ratio": tp2_ratio,
    }


def get_trailing_config(confidence):
    """Return trailing stop percent based on confidence level."""
    if confidence <= 45:
        return {"enabled": True, "trail_percent": 1.0, "move_to_be_after": 1.0}
    if confidence <= 60:
        return {"enabled": True, "trail_percent": 0.5, "move_to_be_after": 1.5}
    if confidence <= 75:
        return {"enabled": True, "trail_percent": 0.3, "move_to_be_after": 1.5}
    return {"enabled": True, "trail_percent": 0.25, "move_to_be_after": 2.0}
