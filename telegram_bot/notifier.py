import asyncio
import nest_asyncio
from telegram import BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
)

from config.telegram_config import TELEGRAM_CHAT_ID, TELEGRAM_TOKEN
from log_setup import logger
from telegram_bot.commands import (
    cmd_balance,
    cmd_equity,
    cmd_logs,
    cmd_pnl,
    cmd_positions,
    cmd_reentry,
    cmd_restart_bot,
    cmd_risk,
    cmd_scanning,
    cmd_start_strategies,
    cmd_status,
    cmd_stop_strategies,
    cmd_strategies,
    cmd_version,
)
from telegram_bot.commands_optimize import cmd_optimize_confidence
from telegram_bot.debug_commands import (
    debug_memory,
    debug_signals,
    debug_status,
    debug_threads,
    debug_weights,
)
from telegram_bot.menu_handler import handle_button
from telegram_bot.menu import build_main_menu

# Обёртка для вызова главного меню
from telegram import Update
from telegram.ext import ContextTypes

async def start_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text("📋 Главное меню:", reply_markup=build_main_menu())

# Разрешаем запуск asyncio внутри уже активного цикла
nest_asyncio.apply()

# Безопасная проверка загрузки токенов без утечек
if TELEGRAM_TOKEN:
    logger.info("✅ TELEGRAM_TOKEN загружен успешно.")
else:
    logger.error("❌ Ошибка: TELEGRAM_TOKEN отсутствует.")

if TELEGRAM_CHAT_ID:
    logger.info("✅ TELEGRAM_CHAT_ID загружен успешно.")
else:
    logger.error("❌ Ошибка: TELEGRAM_CHAT_ID отсутствует.")

# Асинхронный запуск Telegram-бота
async def run_telegram_async() -> None:
    try:
        if TELEGRAM_TOKEN is None:
            raise ValueError("TELEGRAM_TOKEN не установлен")

        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

        await app.bot.set_my_commands([
            BotCommand("start", "📋 Главное меню"),
            BotCommand("start_strategies", "▶️ Запустить стратегии"),
            BotCommand("stop_strategies", "⏹ Остановить стратегии"),
            BotCommand("status", "📊 Проверить статус"),
            BotCommand("strategies", "📘 Активные стратегии"),
            BotCommand("scanning", "🔍 Кто сейчас ищет вход"),
            BotCommand("balance", "💰 Баланс"),
            BotCommand("positions", "📉 Позиции"),
            BotCommand("pnl", "💹 Текущий PnL"),
            BotCommand("logs", "🪵 Логи"),
            BotCommand("restart_bot", "♻️ Перезапуск бота"),
            BotCommand("risk", "🛡 Риск-менеджмент"),
            BotCommand("reentry", "🔁 Повторный вход"),
            BotCommand("version", "📦 Версия"),
            BotCommand("equity", "📈 Equity Curve"),
            BotCommand("optimize_confidence", "🧠 Оптимизация confident весов"),
            BotCommand("debug_status", "🧠 Debug: статус"),
            BotCommand("debug_threads", "📚 Debug: потоки"),
            BotCommand("debug_memory", "📀 Debug: память"),
            BotCommand("debug_weights", "📊 Debug: веса"),
            BotCommand("debug_signals", "🩵 Debug: сигналы"),
        ])

        # ✅ Хендлеры команд
        app.add_handler(CommandHandler("start", start_menu))
        app.add_handler(CommandHandler("menu", start_menu))
        app.add_handler(CommandHandler("start_strategies", cmd_start_strategies))
        app.add_handler(CommandHandler("stop_strategies", cmd_stop_strategies))
        app.add_handler(CommandHandler("status", cmd_status))
        app.add_handler(CommandHandler("strategies", cmd_strategies))
        app.add_handler(CommandHandler("scanning", cmd_scanning))
        app.add_handler(CommandHandler("balance", cmd_balance))
        app.add_handler(CommandHandler("positions", cmd_positions))
        app.add_handler(CommandHandler("pnl", cmd_pnl))
        app.add_handler(CommandHandler("logs", cmd_logs))
        app.add_handler(CommandHandler("restart_bot", cmd_restart_bot))
        app.add_handler(CommandHandler("risk", cmd_risk))
        app.add_handler(CommandHandler("reentry", cmd_reentry))
        app.add_handler(CommandHandler("version", cmd_version))
        app.add_handler(CommandHandler("equity", cmd_equity))
        app.add_handler(CommandHandler("optimize_confidence", cmd_optimize_confidence))

        # 🐞 Хендлеры отладочных команд
        app.add_handler(CommandHandler("debug_status", debug_status))
        app.add_handler(CommandHandler("debug_threads", debug_threads))
        app.add_handler(CommandHandler("debug_memory", debug_memory))
        app.add_handler(CommandHandler("debug_weights", debug_weights))
        app.add_handler(CommandHandler("debug_signals", debug_signals))

        # ⌨️ Кнопки InlineMenu
        app.add_handler(CallbackQueryHandler(handle_button))

        logger.info("🤖 Telegram-бот запущен успешно!")

        if TELEGRAM_CHAT_ID:
            await app.bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text="🤖 Money Sucker Bot запущен и готов к работе. Нажмите /start для управления.",
            )

        await ApplicationBuilder().token(TELEGRAM_TOKEN).build().run_polling()

    except Exception:
        logger.exception("❌ Ошибка при запуске Telegram-бота:")
        raise

# Синхронный запуск
def run_telegram_bot() -> None:
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(run_telegram_async())
        else:
            loop.run_until_complete(run_telegram_async())
    except Exception:
        logger.exception("❌ Ошибка при инициализации Telegram-бота:")
        raise