import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from utils.confidence_optimizer import optimize_confidence_weights
from utils.telegram_utils import send_telegram_message


async def cmd_optimize_confidence(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if update.message:
            await update.message.reply_text("🧠 Начинаю оптимизацию confidence-весов...")

        result = optimize_confidence_weights()

        if isinstance(result, dict):
            message = (
                "✅ <b>Оптимизация завершена!</b>\n"
                f"• Лучшие веса: <code>{result.get('best_weights')}</code>\n"
                f"• Winrate: <b>{result.get('winrate')}%</b>\n"
                f"• Тестов: {result.get('tests_run')}\n"
            )

            if update.message:
                await update.message.reply_text(message, parse_mode=ParseMode.HTML)

            await send_telegram_message("🧠 Confidence веса успешно обновлены.")
        else:
            raise ValueError("Недопустимый формат результата оптимизации")

    except Exception as e:
        error_msg = f"❌ Ошибка оптимизации: {e}"
        if update.message:
            await update.message.reply_text(error_msg)
        await send_telegram_message(f"❌ Ошибка в /optimize_confidence: {e}")
