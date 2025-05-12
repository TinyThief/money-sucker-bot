# config/settings.py

import os
from dotenv import load_dotenv

load_dotenv()

# Боевой режим: если True — ордера отправляются на биржу
LIVE_MODE = os.getenv("LIVE_MODE", "false").lower() == "true"

# Показывать отладку порога уверенности
SHOW_THRESHOLD_DEBUG = os.getenv("SHOW_THRESHOLD_DEBUG", "false").lower() == "true"

# AUTO_TRADE — псевдоним для LIVE_MODE (для совместимости)
AUTO_TRADE = LIVE_MODE

# Глобальный риск на сделку по умолчанию (в процентах)
DEFAULT_RISK_PCT = float(os.getenv("DEFAULT_RISK_PCT", "0.01"))
