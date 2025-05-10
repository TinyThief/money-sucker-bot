import logging
import os

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Проверка без утечки токенов
if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    msg = "❌ Ошибка: Не заданы TELEGRAM_TOKEN или TELEGRAM_CHAT_ID в .env файле"
    raise ValueError(msg)

# Логируем безопасно
logging.info("✅ Telegram токен и чат ID успешно загружены.")
