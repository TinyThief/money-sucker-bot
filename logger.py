import logging
import os

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_PATH = os.path.join(LOG_DIR, "system.log")

# Создаём логгер
logger = logging.getLogger("MoneySuckerBot")
logger.setLevel(logging.INFO)

# Консольный хендлер
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Файловый хендлер
file_handler = logging.FileHandler(LOG_PATH, mode="a", encoding="utf-8")
file_handler.setLevel(logging.INFO)

# Формат логов
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(threadName)s | %(message)s")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Добавляем хендлеры
logger.addHandler(console_handler)
logger.addHandler(file_handler)
