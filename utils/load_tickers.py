import json

from log_setup import logger


async def load_tickers():
    try:
        with open("config/pairs.json", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("pairs", [])
    except Exception as e:
        logger.error(f"Ошибка загрузки pairs.json: {e}")
        return []
