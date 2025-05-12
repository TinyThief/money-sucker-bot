import time
import os
from typing import List, Dict, Any

from telegram import Update
from telegram.ext import ContextTypes

from api.bybit_async import fetch_balance as get_balance, get_open_positions
from core.state import strategy_stop_event
from utils.equity_plot import plot_equity_curve

BOT_START_TIME = time.time()

# ▶️ Управление стратегиями
async def cmd_start_strategies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not strategy_stop_event.is_set():
        if update.message:
            await update.message.reply_text("▶️ Стратегии уже работают.")
        return
    strategy_stop_event.clear()
    if update.message:
        await update.message.reply_text("✅ Стратегии запущены.")

async def cmd_stop_strategies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if strategy_stop_event.is_set():
        if update.message:
            await update.message.reply_text("⛔ Уже остановлены.")
        return
    strategy_stop_event.set()
    if update.message:
        await update.message.reply_text("⏹ Стратегии остановлены.")

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    status = "✅ Активны (ежечасно)" if not strategy_stop_event.is_set() else "⛔ Не запущены"
    if update.message:
        await update.message.reply_text(f"📊 Статус стратегий: {status}")

# 💰 Баланс и позиции
async def cmd_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    balance = await get_balance()
    usdt, free, used = balance if balance else (0.0, 0.0, 0.0)
    if update.message:
        await update.message.reply_text(
            f"💰 Баланс:\n• Total: {usdt:.2f} USDT\n• Free: {free:.2f} USDT\n• Used: {used:.2f} USDT"
        )

async def cmd_positions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    positions = await get_open_positions() or []
    if update.message:
        if not positions:
            await update.message.reply_text("📉 Открытых позиций нет.")
            return
        lines = [
            f"• {p['symbol']}: {p['side']} {p['size']} @ {p['entry']} | PnL: {p.get('pnl', 0.0):.2f}"
            for p in positions
        ]
        await update.message.reply_text("📉 Открытые позиции:\n" + "\n".join(lines))

async def cmd_pnl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    positions = await get_open_positions() or []
    if update.message:
        if not positions:
            await update.message.reply_text("📉 Открытых позиций нет.")
            return
        total_pnl = sum(p.get("pnl", 0.0) for p in positions)
        lines = [f"• {p['symbol']}: {p.get('pnl', 0.0):+.2f}" for p in positions]
        emoji = "🟢" if total_pnl >= 0 else "🔴"
        text = "💹 Текущий PnL:\n" + "\n".join(lines) + f"\n🔽 Общий PnL: {total_pnl:+.2f} USDT {emoji}"
        await update.message.reply_text(text)

# 🔧 Служебные команды
async def cmd_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text("🪵 Логи доступны в папке /logs")

async def cmd_restart_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text("♻️ Перезапуск бота... (заглушка)")

async def cmd_risk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text("🛡 Риск: 1%\nRR: 2.5")

async def cmd_reentry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text("🔁 Повторный вход активирован.")

async def cmd_version(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text("📦 Версия: v3.2")

# 📈 Equity график
async def cmd_equity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    path = plot_equity_curve()
    if update.message:
        if path:
            chat_id = update.effective_chat.id if update.effective_chat else None
            if chat_id:
                with open(path, "rb") as img:
                    await context.bot.send_photo(chat_id=chat_id, photo=img, caption="📈 Equity Curve")
        else:
            await update.message.reply_text("❌ Не удалось построить equity curve.")

# ❤️ Heartbeat
async def cmd_heartbeat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        balance = await get_balance()
        usdt, _, _ = balance if balance else (0.0, 0.0, 0.0)
        positions = await get_open_positions() or []
        total_pnl = sum(p.get("pnl", 0.0) for p in positions)

        uptime_seconds = int(time.time() - BOT_START_TIME)
        uptime_minutes = uptime_seconds // 60
        uptime_hours = uptime_minutes // 60
        uptime_formatted = f"{uptime_hours}ч {uptime_minutes % 60}м"
        strategy_status = "✅ Активны" if not strategy_stop_event.is_set() else "⛔ Остановлены"

        message = (
            "🛡 <b>HEARTBEAT-ОТЧЁТ:</b>\n\n"
            f"• 💰 Баланс: <b>{usdt:.2f} USDT</b>\n"
            f"• 📉 Открытые позиции: <b>{len(positions)}</b>\n"
            f"• 📈 Общий PnL: <b>{total_pnl:+.2f} USDT</b>\n"
            f"• 🧠 Стратегии: <b>{strategy_status}</b>\n"
            f"• ⏰ Аптайм: <b>{uptime_formatted}</b>\n"
            "• ✅ Бот работает нормально."
        )

        if update.message:
            await update.message.reply_text(message, parse_mode="HTML")

    except Exception as e:
        if update.message:
            await update.message.reply_text(f"❌ Ошибка при выполнении heartbeat команды.\n{e}")

# ⛔ Управление pause.flag / halt.flag
async def cmd_pause_trading(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    open("pause.flag", "w").close()
    if update.message:
        await update.message.reply_text("⏸ Торговля приостановлена (pause.flag активен).")

async def cmd_resume_trading(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if os.path.exists("pause.flag"):
        os.remove("pause.flag")
    if update.message:
        await update.message.reply_text("▶️ Торговля возобновлена (pause.flag удалён).")

async def cmd_halt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    open("halt.flag", "w").close()
    if update.message:
        await update.message.reply_text("🛑 Торговля полностью остановлена (halt.flag активен).")

async def cmd_unhalt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if os.path.exists("halt.flag"):
        os.remove("halt.flag")
    if update.message:
        await update.message.reply_text("♻️ Halt снят. Торговля разрешена.")

# 📘 Информационные команды
async def cmd_strategies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text("📘 Активные стратегии:\n- SMC (таймфрейм: 1H)")

async def cmd_scanning(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text("🔍 Сейчас анализируются пары: BTC/USDT, ETH/USDT")
async def cmd_signals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text("🔍 Последние сигналы:\n- BTC/USDT: BUY\n- ETH/USDT: SELL")