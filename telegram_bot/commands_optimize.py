import json
from telegram import Update
from telegram.ext import ContextTypes

from backtest.optimize_confidence import cmd_optimize_confidence_auto


async def cmd_optimize_confidence(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if update.message:
            await update.message.reply_text("🧠 Начинаю оптимизацию confidence-весов...")

        await cmd_optimize_confidence_auto(update, context)

    except Exception as e:
        if update.message:
            await update.message.reply_text(f"❌ Ошибка в /optimize_confidence:\n{e}")
