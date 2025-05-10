from indicators.eqh_eql import find_equal_highs_lows
from indicators.fvg import detect_fvg
from indicators.indicators import get_indicators
from indicators.market_structure import detect_market_structure
from utils.confidence_weights import CONFIDENCE_WEIGHTS
from utils.direction import determine_direction


def get_signal(df):
    """Возвращает торговый сигнал по стратегии SMC на основе переданного DataFrame.
    Включает расчёт confidence на основе весов признаков.
    """
    if len(df) < 50:
        return None

    ms = detect_market_structure(df)
    fvg = detect_fvg(df)
    eq = find_equal_highs_lows(df)
    ind = get_indicators(df)

    if not ms or ms["trend"] == "neutral":
        return None

    direction = determine_direction(ms["trend"], eq.get("liquidity_scenario"))
    if direction == "neutral":
        return None

    reasons = []
    score = 0

    if fvg:
        score += CONFIDENCE_WEIGHTS.get("fvg", 0)
        reasons.append("FVG")
    if eq.get("eqh"):
        score += CONFIDENCE_WEIGHTS.get("eqh", 0)
        reasons.append("EQH")
    if eq.get("eql"):
        score += CONFIDENCE_WEIGHTS.get("eql", 0)
        reasons.append("EQL")
    if ind.get("rsi_extreme"):
        score += CONFIDENCE_WEIGHTS.get("rsi_extreme", 0)
        reasons.append("RSI Extreme")
    if ind.get("macd_cross"):
        score += CONFIDENCE_WEIGHTS.get("macd", 0)
        reasons.append("MACD")
    if ind.get("vwap_bounce"):
        score += CONFIDENCE_WEIGHTS.get("bounce_vwap", 0)
        reasons.append("VWAP Bounce")
    if ind.get("volume_spike"):
        score += CONFIDENCE_WEIGHTS.get("volume_spike", 0)
        reasons.append("Volume Spike")
    if ind.get("ema_filter"):
        score += CONFIDENCE_WEIGHTS.get("ema_filter", 0)
        reasons.append("EMA Filter")

    # Пороговое значение сигнала (например 40)
    if score < 40:
        return None

    return {
        "direction": direction,
        "confidence": score,
        "reasons": reasons,
    }
