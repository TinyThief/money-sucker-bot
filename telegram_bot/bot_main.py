import os
import nest_asyncio
from telegram import BotCommand, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from config.telegram_config import TELEGRAM_CHAT_ID, TELEGRAM_TOKEN
from log_setup import logger
from telegram_bot.commands import (
    cmd_balance,
    cmd_heartbeat,
    cmd_positions,
    cmd_reentry,
    cmd_restart_bot,
    cmd_risk,
    cmd_start_strategies,
    cmd_status,
    cmd_stop_strategies,
    cmd_version,
)
from telegram_bot.commands_optimize import cmd_optimize_confidence
from telegram_bot.debug_commands import (
    debug_memory,
    debug_signals,
    debug_status,
    debug_threads,
    debug_weights,
    cmd_last_signal,
    cmd_equity_plot,
    cmd_drawdown_plot,
    cmd_equity_balance,
    cmd_pnl_summary,
)
from telegram_bot.menu import build_main_menu
from telegram_bot.menu_handler import handle_button

nest_asyncio.apply()

async def start_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text("📂 Главное меню:", reply_markup=build_main_menu())


async def run_telegram_async() -> None:
    if TELEGRAM_TOKEN is None:
        raise ValueError("❌ TELEGRAM_TOKEN не установлен в переменных окружения.")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    await app.bot.set_my_commands([
        BotCommand("start", "📂 Главное меню"),
        BotCommand("start_strategies", "▶️ Запустить стратегии"),
        BotCommand("stop_strategies", "⏹ Остановить стратегии"),
        BotCommand("status", "📊 Статус стратегий"),
        BotCommand("positions", "📈 Открытые позиции"),
        BotCommand("balance", "💰 Баланс счета"),
        BotCommand("restart_bot", "♻️ Перезапуск бота"),
        BotCommand("risk", "🛡 Параметры риска"),
        BotCommand("reentry", "🔁 Повторные входы"),
        BotCommand("version", "📦 Версия бота"),
        BotCommand("optimize_confidence", "🧠 Оптимизация confident весов"),
        BotCommand("heartbeat", "🛡 Статус бота (HEARTBEAT)"),
        BotCommand("debug_status", "🧠 Debug: статус стратегий"),
        BotCommand("debug_threads", "📚 Debug: активные потоки"),
        BotCommand("debug_memory", "📀 Debug: память"),
        BotCommand("debug_weights", "📊 Debug: confident веса"),
        BotCommand("debug_signals", "🔍 Debug: последние сигналы"),
        BotCommand("last_signal", "📄 Последний сигнал по символу"),
        BotCommand("equity_plot", "📈 График Equity Curve"),
        BotCommand("drawdown_plot", "📉 График Drawdown Curve"),
        BotCommand("equity_balance", "💼 Текущий equity баланс"),
        BotCommand("pnl_summary", "📊 Сводка по PnL"),
    ])

    app.add_handler(CommandHandler("start", start_menu))
    app.add_handler(CommandHandler("start_strategies", cmd_start_strategies))
    app.add_handler(CommandHandler("stop_strategies", cmd_stop_strategies))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("positions", cmd_positions))
    app.add_handler(CommandHandler("balance", cmd_balance))
    app.add_handler(CommandHandler("restart_bot", cmd_restart_bot))
    app.add_handler(CommandHandler("risk", cmd_risk))
    app.add_handler(CommandHandler("reentry", cmd_reentry))
    app.add_handler(CommandHandler("version", cmd_version))
    app.add_handler(CommandHandler("optimize_confidence", cmd_optimize_confidence))
    app.add_handler(CommandHandler("heartbeat", cmd_heartbeat))
    app.add_handler(CommandHandler("debug_status", debug_status))
    app.add_handler(CommandHandler("debug_threads", debug_threads))
    app.add_handler(CommandHandler("debug_memory", debug_memory))
    app.add_handler(CommandHandler("debug_weights", debug_weights))
    app.add_handler(CommandHandler("debug_signals", debug_signals))
    app.add_handler(CommandHandler("last_signal", cmd_last_signal))
    app.add_handler(CommandHandler("equity_plot", cmd_equity_plot))
    app.add_handler(CommandHandler("drawdown_plot", cmd_drawdown_plot))
    app.add_handler(CommandHandler("equity_balance", cmd_equity_balance))
    app.add_handler(CommandHandler("pnl_summary", cmd_pnl_summary))
    app.add_handler(CallbackQueryHandler(handle_button))

    logger.info("Telegram-бот запущен!")

    try:
        if TELEGRAM_CHAT_ID:
            await app.bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text="Бот успешно запущен! Нажмите /start для управления."
            )
        else:
            logger.warning("⚠️ TELEGRAM_CHAT_ID не задан. Стартовое сообщение не отправлено.")
    except Exception as e:
        logger.warning(f"[Telegram] Ошибка отправки стартового сообщения: {e}")

    app.run_polling()


async def start_telegram() -> None:
    try:
        await run_telegram_async()
    except Exception:
        logger.exception("Ошибка при запуске Telegram-бота:")


if __name__ == "__main__":
    import asyncio
    asyncio.run(start_telegram())