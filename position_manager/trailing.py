from log_setup import logger


def calculate_trailing_stop(entry: float, direction: str, trail_percent: float, current_price: float) -> float:
    """Рассчитывает новый уровень стоп-лосса для трейлинга позиции.

    :param entry: Цена входа в позицию
    :param direction: Направление сделки: 'long' или 'short'
    :param trail_percent: Процент трейлинга, например, 0.01 для 1%
    :param current_price: Текущая рыночная цена
    :return: Новая цена стоп-лосса
    """
    if direction == "long":
        stop = current_price * (1 - trail_percent)
        # Защищаем: стоп не может быть ниже допустимого минимального уровня
        return round(max(stop, entry * (1 - trail_percent)), 4)

    if direction == "short":
        stop = current_price * (1 + trail_percent)
        # Защищаем: стоп не может быть выше допустимого максимального уровня
        return round(min(stop, entry * (1 + trail_percent)), 4)

    logger.warning(f"❓ Неверное направление для трейлинга: {direction}. Возвращаю цену входа без изменений.")
    return round(entry, 4)
