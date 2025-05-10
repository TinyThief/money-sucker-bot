from typing import Optional

def determine_direction(
    market_structure: Optional[str],
    liquidity_scenario: Optional[str] = None
) -> str:
    """
    Определяет торговое направление ("long", "short", "neutral")
    на основе структуры рынка и сценария ликвидности.

    :param market_structure: "bullish", "bearish" или None
    :param liquidity_scenario: "above_eqh", "below_eql" и их комбинации (опционально)
    """
    if not market_structure:
        return "neutral"

    ms = market_structure.strip().lower()
    ls = liquidity_scenario.strip().lower().replace(" ", "_") if liquidity_scenario else ""

    # Конфликтные сценарии ликвидности
    if ms == "bullish" and "above_eqh" in ls:
        return "long"
    if ms == "bearish" and "below_eql" in ls:
        return "short"
    if ms == "bullish" and "below_eql" in ls:
        return "neutral"
    if ms == "bearish" and "above_eqh" in ls:
        return "neutral"

    # По структуре рынка без фильтров
    if ms == "bullish":
        return "long"
    if ms == "bearish":
        return "short"

    return "neutral"
