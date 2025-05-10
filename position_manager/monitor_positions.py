import asyncio
from typing import Literal

from telegram.error import TelegramError

from api.bybit_async import get_current_price, get_open_positions, update_stop_loss
from log_setup import logger
from position_manager.trailing import calculate_trailing_stop
from utils.telegram_utils import send_telegram_message

TRAILING_START_RR = 1.5
TRAILING_DISTANCE = 0.005
CHECK_INTERVAL = 10

monitored_positions = set()


async def monitor_all_positions() -> None:
    logger.info("🚦 Запуск мониторинга всех открытых позиций...")

    while True:
        try:
            positions = await get_open_positions()
            for p in positions:
                symbol = p["symbol"]
                if symbol not in monitored_positions and p["size"] > 0:
                    asyncio.create_task(monitor_single_position(
                        symbol=symbol,
                        tp1=p.get("tp1"),
                        tp2=p.get("tp2"),
                        entry=p.get("entry_price"),
                        direction=p.get("side"),
                        stop_loss=p.get("stop_loss"),
                    ))
                    monitored_positions.add(symbol)

        except (ValueError, RuntimeError) as e:
            logger.error("❌ Ошибка мониторинга всех позиций: %s", str(e))

        await asyncio.sleep(CHECK_INTERVAL)


async def monitor_single_position(
    symbol: str,
    tp1: float | None,
    tp2: float | None,
    entry: float | None,
    direction: Literal["long", "short"],
    stop_loss: float | None,
) -> None:
    logger.info("▶️ Начат мониторинг позиции: %s", symbol)
    moved_to_be = False
    last_sl = stop_loss if stop_loss is not None else entry

    while True:
        try:
            positions = await get_open_positions()
            current = next((p for p in positions if p["symbol"] == symbol), None)

            if not current or current.get("size", 0) == 0:
                logger.info("💚 Позиция по %s закрыта. Завершаем мониторинг.", symbol)
                monitored_positions.discard(symbol)
                break

            current_price = await get_current_price(symbol)

            if entry is None or current_price is None or last_sl is None:
                logger.warning("⚠️ Пропуск расчета RR для %s: отсутствуют entry/price/SL.", symbol)
                await asyncio.sleep(CHECK_INTERVAL)
                continue

            rr_now = abs(current_price - entry) / abs(entry - last_sl)

            if not moved_to_be and rr_now >= 1.0:
                be_price = entry
                await update_stop_loss(symbol, be_price)
                logger.info("🛡️ SL перенесён в безубыток по %s на %.4f", symbol, be_price)
                await safe_send(f"🛡️ SL перенесён в безубыток: {symbol} → {be_price}")
                moved_to_be = True

            if moved_to_be and rr_now >= TRAILING_START_RR:
                new_sl = calculate_trailing_stop(entry, direction, TRAILING_DISTANCE, current_price)
                if (direction == "long" and new_sl > last_sl) or (direction == "short" and new_sl < last_sl):
                    await update_stop_loss(symbol, new_sl)
                    logger.info("🔁 Трейлинг-SL обновлён по %s: %.4f", symbol, new_sl)
                    await safe_send(f"🔁 Трейлинг-SL обновлён по {symbol}: {new_sl}")
                    last_sl = new_sl

        except (ValueError, RuntimeError) as e:
            logger.error("⚡️ Ошибка в мониторинге позиции %s: %s", symbol, str(e))

        await asyncio.sleep(CHECK_INTERVAL)


async def safe_send(text: str) -> None:
    try:
        await send_telegram_message(text)
    except TelegramError as e:
        logger.error("❌ Ошибка отправки Telegram сообщения: %s", str(e))
