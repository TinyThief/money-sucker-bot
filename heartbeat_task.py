import asyncio

from api.bybit_async import get_open_positions
from log_setup import logger
from utils.telegram_utils import send_telegram_message

BASE_HEARTBEAT_INTERVAL_MINUTES = 10
ACTIVE_HEARTBEAT_INTERVAL_MINUTES = 5
IDLE_HEARTBEAT_INTERVAL_MINUTES = 20

async def start_heartbeat() -> None:
    logger.info("💓 Запущен Адаптивный Heartbeat-процесс.")

    while True:
        try:
            positions = await get_open_positions()
            num_positions = len(positions) if positions else 0

            if num_positions >= 1:
                interval = ACTIVE_HEARTBEAT_INTERVAL_MINUTES
                logger.info(f"📈 Найдены открытые позиции: {num_positions}. Устанавливаем Heartbeat каждые {interval} минут.")
            else:
                interval = IDLE_HEARTBEAT_INTERVAL_MINUTES
                logger.info(f"😴 Позиции не найдены. Устанавливаем Heartbeat каждые {interval} минут.")

            await send_telegram_message("💓 Heartbeat: Бот активен ✅")
        except Exception as e:
            logger.warning(f"Ошибка отправки Heartbeat: {e}")
            interval = BASE_HEARTBEAT_INTERVAL_MINUTES

        await asyncio.sleep(interval * 60)

