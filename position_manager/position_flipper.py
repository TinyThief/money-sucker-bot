import asyncio

from trade_executor_core import close_position, get_open_position
from config.settings import AUTO_TRADE
from log_setup import logger
from trade_executor_core import place_order
from utils.safe_tools import safe_execute
from utils.telegram_utils import send_telegram_message


def flip_position(
    symbol: str,
    new_side: str,
    size: float,
    sl: float,
    tp: float,
    tp1: float | None = None,
    tp2: float | None = None,
    tp1_ratio: float = 0.5,
) -> bool:
    """Переворачивает позицию по символу с поддержкой TP1/TP2."""
    async def _execute():
        current = await safe_execute(get_open_position, symbol=symbol)
        if not current or current.get("size", 0) == 0:
            logger.info("🟢 Нет позиции по %s — открываем %s", symbol, new_side.upper())
            await _notify(f"📈 <b>{symbol}</b>: открытие позиции {new_side.upper()} без переворота.")
            return await _open(symbol, new_side, size, sl, tp1, tp2, tp1_ratio)

        current_side = current.get("side", "").lower()
        if (current_side == "long" and new_side == "buy") or (current_side == "short" and new_side == "sell"):
            logger.info("⚠️ Позиция по %s уже открыта в направлении %s. Переворот не нужен.", symbol, current_side.upper())
            return False

        logger.info("🔁 Переворот: %s — закрытие %s, открытие %s", symbol, current_side.upper(), new_side.upper())
        await _notify(f"🔁 <b>{symbol}</b>: переворот позиции — {current_side.upper()} ➜ {new_side.upper()}")

        closed = await safe_execute(close_position, symbol=symbol)
        if not closed:
            logger.error("❌ Ошибка закрытия позиции по %s. Переворот отменён.", symbol)
            return False

        return await _open(symbol, new_side, size, sl, tp1, tp2, tp1_ratio)

    return asyncio.run(_execute())


async def _open(
    symbol: str,
    side: str,
    size: float,
    sl: float,
    tp1: float | None = None,
    tp2: float | None = None,
    tp1_ratio: float = 0.5,
) -> bool:
    if not AUTO_TRADE:
        logger.info("🟡 DRY-RUN: позиция %s по %s, объём %.2f", side.upper(), symbol, size)
        return True

    result = await safe_execute(place_order, symbol, side, size, sl, tp2, tp1, tp1_ratio)
    if result:
        logger.info("✅ Открыта позиция %s по %s, объём %.2f", side.upper(), symbol, size)
        return True

    logger.error("❌ Не удалось открыть позицию %s по %s", side.upper(), symbol)
    return False


async def _notify(text: str) -> None:
    if AUTO_TRADE:
        await send_telegram_message(text)
