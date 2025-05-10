import asyncio

from api.bybit_async import fetch_balance as get_balance
from log_setup import logger
from utils.telegram_utils import send_telegram_message

BALANCE_CHECK_INTERVAL_SECONDS = 60
BALANCE_CHANGE_THRESHOLD_PERCENT = 5  # Пороговое изменение баланса в процентах

last_balance = None

async def monitor_balance_status() -> None:
    global last_balance

    while True:
        await asyncio.sleep(BALANCE_CHECK_INTERVAL_SECONDS)
        try:
            usdt, free, used = await get_balance()
            if usdt is not None:
                if last_balance is None:
                    last_balance = usdt
                    logger.info(f"💰 Начальный баланс установлен: {usdt:.2f} USDT")
                else:
                    change_percent = ((usdt - last_balance) / last_balance) * 100

                    if abs(change_percent) >= BALANCE_CHANGE_THRESHOLD_PERCENT:
                        if change_percent < 0:
                            msg = f"🚨 Баланс упал на {abs(change_percent):.2f}%!\nТекущий баланс: {usdt:.2f} USDT"
                        else:
                            msg = f"🤑 Баланс вырос на {change_percent:.2f}%!\nТекущий баланс: {usdt:.2f} USDT"

                        await send_telegram_message(msg)
                        logger.warning(msg)

                        last_balance = usdt  # Обновляем баланс после уведомления
            else:
                logger.warning("⚠️ Не удалось получить баланс для мониторинга.")
        except Exception as e:
            logger.error(f"Ошибка в monitor_balance_status: {e}")
