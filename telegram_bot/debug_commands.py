import json
import os
import threading
import psutil
import pandas as pd
import matplotlib.pyplot as plt

from collections import defaultdict
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from core import state
from utils.confidence_weights import CONFIDENCE_WEIGHTS as default_weights

SIGNAL_LOG_PATH = "logs/signal_log.csv"
DEBUG_LOG_PATH = "logs/signal_debug.log"
EQUITY_CSV_PATH = "data/equity_curve.csv"
BACKTESTS_DIR = "backtests"

# Безопасные ответы
async def safe_reply(update: Update, text: str, **kwargs):
    if update.message:
        await update.message.reply_text(text, **kwargs)

async def safe_reply_photo(update: Update, photo: InputFile, caption: str = ""):
    if update.message:
        await update.message.reply_photo(photo=photo, caption=caption)

# /debug status
async def debug_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await safe_reply(update,
        f"✅ Бот активен: {state.is_running}\n"
        f"🧵 Стратегия поток: {'✅' if state.strategy_thread and state.strategy_thread.is_alive() else '❌'}\n"
        f"🛑 Stop Event: {state.strategy_stop_event.is_set()}"
    )

# /debug threads
async def debug_threads(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    threads = threading.enumerate()
    msg = "\n".join([f"• {t.name}" for t in threads])
    await safe_reply(update, f"🧵 Активные потоки:\n{msg}")

# /debug memory
async def debug_memory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    process = psutil.Process(os.getpid())
    mem_mb = process.memory_info().rss / 1024 / 1024
    await safe_reply(update, f"📦 Используемая память: {mem_mb:.2f} MB")

# /debug weights
async def debug_weights(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    formatted = json.dumps(default_weights, indent=2)
    await safe_reply(update, f"📊 Текущие веса признаков:\n<pre>{formatted}</pre>", parse_mode="HTML")

# /debug signals
async def debug_signals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        with open(SIGNAL_LOG_PATH, encoding="utf-8") as f:
            lines = f.readlines()[-5:]
        msg = "\n".join(lines)
        await safe_reply(update, f"🪵 Последние сигналы:\n<pre>{msg}</pre>", parse_mode="HTML")
    except Exception as e:
        await safe_reply(update, f"❌ Ошибка при чтении сигналов: {e}")

# /last_signal SYMBOL
async def cmd_last_signal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await safe_reply(update, "⚠️ Укажите символ, пример: /last_signal BTC/USDT")
        return

    symbol = context.args[0].upper()

    if not os.path.exists(DEBUG_LOG_PATH):
        await safe_reply(update, "❌ Лог сигналов не найден.")
        return

    try:
        with open(DEBUG_LOG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line in reversed(lines):
            if symbol in line:
                await safe_reply(update, f"📄 Последний сигнал по {symbol}:\n<code>{line.strip()}</code>", parse_mode="HTML")
                return

        await safe_reply(update, f"ℹ️ Нет записей по {symbol} в логе.")
    except Exception as e:
        await safe_reply(update, f"❌ Ошибка чтения лога: {e}")

# /equity_plot
async def cmd_equity_plot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not os.path.exists(EQUITY_CSV_PATH):
        await safe_reply(update, "❌ Файл equity_curve.csv не найден.")
        return
    try:
        df = pd.read_csv(EQUITY_CSV_PATH)
        if df.empty or 'equity' not in df.columns:
            await safe_reply(update, "⚠️ Неверный формат equity-файла.")
            return

        plt.figure(figsize=(10, 5))
        plt.plot(df['equity'], label='Equity')
        plt.title('Equity Curve')
        plt.xlabel('Trade #')
        plt.ylabel('Equity')
        plt.grid(True)
        plt.legend()

        plot_path = "logs/equity_plot.png"
        plt.savefig(plot_path)
        plt.close()

        with open(plot_path, "rb") as img:
            if update.message:
                await update.message.reply_photo(InputFile(img), caption="📈 Equity Curve")
    except Exception as e:
        await safe_reply(update, f"❌ Ошибка при построении графика: {e}")

# /drawdown_plot
async def cmd_drawdown_plot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not os.path.exists(EQUITY_CSV_PATH):
        await safe_reply(update, "❌ Файл equity_curve.csv не найден.")
        return
    try:
        df = pd.read_csv(EQUITY_CSV_PATH)
        if df.empty or 'equity' not in df.columns:
            await safe_reply(update, "⚠️ Неверный формат equity-файла.")
            return

        equity = df['equity']
        rolling_max = equity.cummax()
        drawdown = (equity - rolling_max) / rolling_max

        plt.figure(figsize=(10, 5))
        plt.plot(drawdown, label='Drawdown', color='red')
        plt.title('Drawdown Curve')
        plt.xlabel('Trade #')
        plt.ylabel('Drawdown (fraction)')
        plt.grid(True)
        plt.legend()

        plot_path = "logs/drawdown_plot.png"
        plt.savefig(plot_path)
        plt.close()

        with open(plot_path, "rb") as img:
            if update.message:
                await update.message.reply_photo(InputFile(img), caption="📉 Drawdown Curve")
    except Exception as e:
        await safe_reply(update, f"❌ Ошибка при построении drawdown-графика: {e}")

# /equity_balance
async def cmd_equity_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not os.path.exists(EQUITY_CSV_PATH):
        await safe_reply(update, "❌ Файл equity_curve.csv не найден.")
        return
    try:
        df = pd.read_csv(EQUITY_CSV_PATH)
        if df.empty or 'equity' not in df.columns:
            await safe_reply(update, "⚠️ Неверный формат equity-файла.")
            return

        current_equity = df['equity'].iloc[-1]
        await safe_reply(update, f"💼 Текущий баланс equity: {current_equity:.2f} USDT")
    except Exception as e:
        await safe_reply(update, f"❌ Ошибка при чтении equity: {e}")

# /pnl_summary
async def cmd_pnl_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not os.path.exists(SIGNAL_LOG_PATH):
        await safe_reply(update, "❌ Лог сигналов не найден.")
        return
    try:
        df = pd.read_csv(SIGNAL_LOG_PATH, header=None)
        df.columns = [
            "timestamp", "symbol", "direction", "entry_price", "sl_price", "tp_price",
            "size", "confidence", "reasons", "status", "result", "pnl"
        ]

        trades = df.dropna(subset=["pnl"])
        total_trades = len(trades)
        total_pnl = trades["pnl"].sum()
        win_rate = (trades["pnl"] > 0).mean() * 100
        avg_rr = trades.apply(lambda row: abs((row["tp_price"] - row["entry_price"]) / (row["entry_price"] - row["sl_price"])) if row["entry_price"] != row["sl_price"] else 0, axis=1).mean()

        msg = (
            f"📊 Сводка PnL:\n"
            f"• Сделок: {total_trades}\n"
            f"• Общий PnL: {total_pnl:.2f} USDT\n"
            f"• Winrate: {win_rate:.1f}%\n"
            f"• Средний Risk/Reward: {avg_rr:.2f}"
        )
        await safe_reply(update, msg)
    except Exception as e:
        await safe_reply(update, f"❌ Ошибка при обработке PnL: {e}")

# /summary_plot
async def cmd_summary_plot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        df = pd.read_csv(SIGNAL_LOG_PATH, header=None)
        df.columns = [
            "timestamp", "symbol", "direction", "entry_price", "sl_price", "tp_price",
            "size", "confidence", "reasons", "status", "result", "pnl"
        ]
        df['pnl'].hist(bins=50)
        plt.title("PNL Histogram")
        plt.grid(True)
        plt.savefig("logs/pnl_histogram.png")
        plt.close()

        with open("logs/pnl_histogram.png", "rb") as img:
            if update.message:
                await update.message.reply_photo(InputFile(img), caption="📊 Распределение PnL")
    except Exception as e:
        await safe_reply(update, f"❌ Ошибка при построении сводного графика: {e}")

# /cmd_optimize_confidence
async def cmd_optimize_confidence_auto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not os.path.exists(SIGNAL_LOG_PATH):
        await safe_reply(update, "❌ Лог сигналов не найден.")
        return

    try:
        df = pd.read_csv(SIGNAL_LOG_PATH, header=None)
        df.columns = [
            "timestamp", "symbol", "direction", "entry_price", "sl_price", "tp_price",
            "size", "confidence", "reasons", "status", "result", "pnl"
        ]

        counts = defaultdict(lambda: {"tp": 0, "sl": 0})
        for _, row in df.iterrows():
            if row["result"] not in ["tp", "sl"]:
                continue
            reason_list = str(row["reasons"]).split("; ")
            for reason in reason_list:
                if row["result"] == "tp":
                    counts[reason]["tp"] += 1
                else:
                    counts[reason]["sl"] += 1

        weights = {}
        for reason, stats in counts.items():
            total = stats["tp"] + stats["sl"]
            score = 50 if total == 0 else int(stats["tp"] / total * 100)
            weights[reason] = score

        os.makedirs("config", exist_ok=True)
        with open("config/confidence_weights.json", "w", encoding="utf-8") as f:
            json.dump(weights, f, indent=4)

        await safe_reply(update, "🧠 Веса confident успешно переобучены и сохранены в config/confidence_weights.json")
    except Exception as e:
        await safe_reply(update, f"❌ Ошибка оптимизации confident-весов: {e}")

# /load_weights
async def cmd_load_weights(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if not os.path.exists(BACKTESTS_DIR):
            await safe_reply(update, "📂 Папка backtests пуста.")
            return

        folders = sorted(os.listdir(BACKTESTS_DIR), reverse=True)
        if not folders:
            await safe_reply(update, "❌ Нет сохранённых весов для загрузки.")
            return

        keyboard = [
            [InlineKeyboardButton(f"📥 {folder}", callback_data=f"load_weights:{folder}")]
            for folder in folders[:5]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        await safe_reply(update, "🔄 Выбери версию весов для загрузки:", reply_markup=markup)

    except Exception as e:
        await safe_reply(update, f"❌ Ошибка при загрузке весов: {e}")

# Обработчик кнопок загрузки
async def handle_button_load_weights(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.data or not query.data.startswith("load_weights:"):
        return

    await query.answer()
    try:
        folder = query.data.split(":", 1)[1]
        weights_path = os.path.join(BACKTESTS_DIR, folder, "best_weights.json")
        if not os.path.exists(weights_path):
            await query.edit_message_text(f"❌ Файл не найден: {weights_path}")
            return

        with open(weights_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            weights = data.get("weights", {})

        os.makedirs("config", exist_ok=True)
        with open("config/confidence_weights.json", "w", encoding="utf-8") as f:
            json.dump(weights, f, indent=4)

        await query.edit_message_text(f"✅ Загружены веса из {folder} и применены как активные.")
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка при применении весов: {e}")
