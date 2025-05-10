import json
import traceback

from log_setup import logger  # предполагается, что логгер уже настроен
from strategies.smc_strategy import run_smc_strategy


# 📦 Загрузка символов из config/pairs.json
def load_symbols():
    try:
        with open("config/pairs.json", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("pairs", [])
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки pairs.json: {e}")
        return []

symbols = load_symbols()

CAPITAL = 1000
RISK_PCT = 0.01

logger.info("🟢 Запуск стратегии SMC для нескольких пар...")

for symbol in symbols:
    try:
        logger.info(f"\n🟡 Старт обработки {symbol}")
        run_smc_strategy(symbol=symbol, capital=CAPITAL, risk_pct=RISK_PCT)
        logger.info(f"✅ Завершено {symbol}")
    except Exception as e:
        logger.exception(f"❌ Ошибка в работе стратегии для {symbol}: {e!s}")
        traceback.print_exc()

logger.info("🟣 Все стратегии завершены.")
