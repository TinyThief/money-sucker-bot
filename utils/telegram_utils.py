import os
import asyncio
from telegram.ext import Application
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN") or ""
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID") or ""

if not TELEGRAM_TOKEN:
    raise RuntimeError("❌ TELEGRAM_TOKEN не установлен в .env")
if not TELEGRAM_CHAT_ID:
    raise RuntimeError("❌ TELEGRAM_CHAT_ID не установлен в .env")

application = Application.builder().token(TELEGRAM_TOKEN).build()
bot = application.bot

__all__ = [
    "send_telegram_message",
    "send_telegram_photo",
    "notify_entry",
    "notify_take_profit",
    "notify_stop_loss",
    "notify_manual_close",
    "notify_pnl",
]

# Убедитесь, что все модули проекта импортируют send_telegram_message и другие уведомления
# именно отсюда: from utils.telegram_utils import send_telegram_message, ...
# Старый модуль telegram_sender должен быть удалён и не использоваться.

async def send_telegram_message(message: str, parse_mode: str = "HTML"):
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode=parse_mode)

    except Exception as e:
        print(f"❌ Ошибка при отправке сообщения в Telegram: {e}")

async def send_telegram_photo(image_path: str, caption: str = ""): 
    try:
        with open(image_path, "rb") as photo:
            await bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=photo, caption=caption)
    except Exception as e:
        print(f"❌ Ошибка при отправке фото в Telegram: {e}")

async def notify_entry(symbol: str, side: str, size: float, price: float):
    text = (
        f"🚀 <b>ВХОД В СДЕЛКУ</b>\n"
        f"• <b>{symbol}</b> {side.upper()}\n"
        f"• Объём: <b>{size}</b>\n"
        f"• Цена входа: <b>{price}</b>"
    )
    await send_telegram_message(text)

async def notify_take_profit(symbol: str, qty: float, price: float):
    text = (
        f"🎯 <b>TP</b> по <b>{symbol}</b>\n"
        f"• Объём: <b>{qty}</b>\n"
        f"• Цена: <b>{price}</b>"
    )
    await send_telegram_message(text)

async def notify_stop_loss(symbol: str, qty: float, price: float):
    text = (
        f"🛑 <b>SL</b> по <b>{symbol}</b>\n"
        f"• Объём: <b>{qty}</b>\n"
        f"• Цена: <b>{price}</b>"
    )
    await send_telegram_message(text)

async def notify_manual_close(symbol: str):
    text = f"🚪 Позиция по <b>{symbol}</b> закрыта вручную."
    await send_telegram_message(text)

async def notify_pnl(symbol: str, pnl: float):
    emoji = "🟢" if pnl >= 0 else "🔴"
    text = f"{emoji} <b>Итог по {symbol}</b>: PnL = <b>{pnl:.2f} USDT</b>"
    await send_telegram_message(text)
