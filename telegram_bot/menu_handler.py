from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.commands import *
from backtest.optimize_confidence import *
from telegram_bot.debug_commands import *
from telegram_bot.menu import *
from utils.telegram_utils import send_telegram_message

# Безопасный вызов edit_message_text
async def safe_edit_message_text(update: Update, text: str, **kwargs):
    if update.callback_query and update.callback_query.message:
        await update.callback_query.edit_message_text(text=text, **kwargs)

# Async handlers
async def handler_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_edit_message_text(update, "📂 Главное меню:", reply_markup=build_main_menu())

async def handler_menu_strategies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_edit_message_text(update, "📈 Стратегии:", reply_markup=build_strategy_menu())

async def handler_menu_monitoring(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_edit_message_text(update, "📊 Мониторинг:", reply_markup=build_monitoring_menu())

async def handler_menu_risk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_edit_message_text(update, "🛡 Управление рисками:", reply_markup=build_risk_menu())

async def handler_menu_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_edit_message_text(update, "⚙️ Настройки:", reply_markup=build_settings_menu())

async def handler_scanning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_telegram_message("🔍 Сканирование запущено.")

# Карта callback-команд к функциям
COMMAND_HANDLERS = {
    "menu": handler_menu,
    "menu_strategies": handler_menu_strategies,
    "menu_monitoring": handler_menu_monitoring,
    "menu_risk": handler_menu_risk,
    "menu_settings": handler_menu_settings,

    # Стратегии
    "start_strategies": cmd_start_strategies,
    "stop_strategies": cmd_stop_strategies,
    "scanning": handler_scanning,

    # Мониторинг
    "status": cmd_status,
    "positions": cmd_positions,
    "balance": cmd_balance,
    "heartbeat": cmd_heartbeat,
    "logs": debug_signals,
    "equity_curve": cmd_equity_plot,
    "summary_plot": cmd_summary_plot,

    # Риски
    "risk": cmd_risk,
    "reentry": cmd_reentry,
    "pnl_summary": cmd_pnl_summary,

    # Настройки
    "optimize_confidence": cmd_optimize_confidence,
    "optimize_confidence_auto": cmd_optimize_confidence_auto,
    "version": cmd_version,
    "restart_bot": cmd_restart_bot,
}

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return

    await query.answer()
    data = query.data or ""

    if data.startswith("load_weights:"):
        await handle_button_load_weights(update, context)
        return

    handler = COMMAND_HANDLERS.get(data)
    if handler:
        await handler(update, context)
        return

    await safe_edit_message_text(update, "❓ Неизвестная команда. Возможно, кнопка устарела.")
