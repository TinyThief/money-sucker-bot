import logging
import os
import sys

os.makedirs("logs", exist_ok=True)

# 🔴 Лог только ошибок
error_handler = logging.FileHandler("logs/error.log", encoding="utf-8", errors="replace")
error_handler.setLevel(logging.ERROR)

# 🟢 Основной лог
file_handler = logging.FileHandler("logs/bot.log", encoding="utf-8", errors="replace")
file_handler.setLevel(logging.INFO)

# 🖥️ Вывод в консоль
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[file_handler, error_handler, console_handler],
)

logger = logging.getLogger("MoneySuckerBot")