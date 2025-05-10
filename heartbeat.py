import time

from telegram import Update
from telegram.ext import ContextTypes

from api.bybit_async import fetch_balance, get_open_positions
from core.state import strategy_stop_event

BOT_START_TIME = time.time()

# 🛡 Heartbeat - Статус бота
async def cmd_heartbeat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        balance = await fetch_balance()
        if balance is None:
            if update.message:
                await update.message.reply_text("❌ Ошибка: не удалось получить баланс.")
            return
        usdt, free, used = balance
        positions = await get_open_positions()

        total_pnl = sum(p["pnl"] for p in positions) if positions else 0
        uptime_seconds = int(time.time() - BOT_START_TIME)
        uptime_minutes = uptime_seconds // 60
        uptime_hours = uptime_minutes // 60
        uptime_formatted = f"{uptime_hours}ч {uptime_minutes % 60}м"

        strategy_status = "✅ Активны" if not strategy_stop_event.is_set() else "⛔ Остановлены"

        message = (
            "🛡 <b>HEARTBEAT-ОТЧЁТ:</b>\n\n"
            f"• 💰 Баланс: <b>{usdt:.2f} USDT</b>\n"
            f"• 📉 Открытые позиции: <b>{len(positions) if positions else 0}</b>\n"
            f"• 📈 Общий PnL: <b>{total_pnl:+.2f} USDT</b>\n"
            f"• 🧠 Стратегии: <b>{strategy_status}</b>\n"
            f"• ⏰ Аптайм: <b>{uptime_formatted}</b>\n"
            "• ✅ Бот работает нормально."
        )

        if update.message:
            await update.message.reply_text(message, parse_mode="HTML")

    except Exception:
        if update.message:
            await update.message.reply_text("❌ Ошибка при получении heartbeat статуса.")
