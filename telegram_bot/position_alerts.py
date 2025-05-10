from log_setup import logger
from telegram_bot.alert_utils import send_telegram_alert
from typing import Optional, Awaitable

# 🔔 Уведомление о закрытии позиции по TP
async def notify_take_profit(symbol: str, qty: float, price: float) -> None:
    msg = (
        f"✅ TP достигнут по <b>{symbol}</b>\n"
        f"Объём: <code>{qty}</code> по цене <code>{price}</code>"
    )
    logger.info(f"[ALERT] {msg}")
    if callable(send_telegram_alert):
        result: Optional[Awaitable] = send_telegram_alert(msg)
        if result:
            await result


# 🔔 Уведомление о закрытии позиции по SL
async def notify_stop_loss(symbol: str, qty: float, price: float) -> None:
    msg = (
        f"🛑 SL сработал по <b>{symbol}</b>\n"
        f"Объём: <code>{qty}</code> по цене <code>{price}</code>"
    )
    logger.info(f"[ALERT] {msg}")
    if callable(send_telegram_alert):
        result: Optional[Awaitable] = send_telegram_alert(msg)
        if result:
            await result


# 🔔 Уведомление о ручном закрытии позиции
async def notify_manual_close(symbol: str) -> None:
    msg = f"📤 Позиция по <b>{symbol}</b> была закрыта вручную."
    logger.info(f"[ALERT] {msg}")
    if callable(send_telegram_alert):
        result: Optional[Awaitable] = send_telegram_alert(msg)
        if result:
            await result


# 🔔 Уведомление о Flip-позиции
async def notify_flip(symbol: str, from_side: str, to_side: str) -> None:
    msg = (
        f"🔄 Flip по <b>{symbol}</b>\n"
        f"{from_side.upper()} ➔ {to_side.upper()}"
    )
    logger.info(f"[ALERT] {msg}")
    if callable(send_telegram_alert):
        result: Optional[Awaitable] = send_telegram_alert(msg)
        if result:
            await result