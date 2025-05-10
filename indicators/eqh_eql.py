import pandas as pd


def find_equal_highs_lows(df: pd.DataFrame, precision: int = 2):
    """Находит Equal Highs / Lows (EQH / EQL) и определяет сценарий ликвидности.

    :param df: DataFrame с историей свечей.
    :param precision: точность округления для сравнения high/low.
    :return: словарь с признаками и сценарием ликвидности.
    """
    eqh = False
    eql = False
    liquidity_scenario = None

    # Округляем high/low для упрощения поиска дубликатов
    rounded_highs = df["high"].round(precision)
    rounded_lows = df["low"].round(precision)

    # Ищем повторяющиеся high/low
    eqh_count = rounded_highs.duplicated(keep=False).sum()
    eql_count = rounded_lows.duplicated(keep=False).sum()

    if eqh_count >= 3:
        eqh = True
    if eql_count >= 3:
        eql = True

    # Сценарий ликвидности (если текущая цена выносит экстремумы)
    if eqh and df["high"].iloc[-1] > rounded_highs.max():
        liquidity_scenario = "Sweep EQH"
    elif eql and df["low"].iloc[-1] < rounded_lows.min():
        liquidity_scenario = "Sweep EQL"

    return {
        "eqh": eqh,
        "eql": eql,
        "liquidity_scenario": liquidity_scenario,
    }
