from telegram import Update
from telegram.ext import ContextTypes

from utils.equity_plot import plot_equity_curve


async def cmd_equity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    image = plot_equity_curve()
    if image and update.message:
        await update.message.reply_photo(photo=image, caption="📈 Equity Curve")
    elif update.message:
        await update.message.reply_text("⚠️ Недостаточно данных для построения графика.")
