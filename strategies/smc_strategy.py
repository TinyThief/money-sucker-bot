import json
import time
import pandas as pd
import os

from api.bybit_async import get_ohlcv, get_current_price
from indicators.market_structure import detect_market_structure
from log_setup import logger
from monitor_liquidations import monitoring_only_mode
from utils.direction import determine_direction
from utils.dynamic_sl_tp import get_dynamic_sl_tp
from utils.liquidation_ws import recent_liquidations
from utils.risk_limits import risk_limits_exceeded
from utils.volume import check_volume_spike
from trade_executor_core import place_order, risk_manager

try:
    with open("config/best_weights.json") as f:
        CONFIDENCE_WEIGHTS = json.load(f)
except FileNotFoundError:
    from utils.confidence_weights import CONFIDENCE_WEIGHTS

ENTRY_CACHE: dict[str, dict] = {}
ENTRY_TIMEOUT = 60 * 30

DEBUG_LOG_PATH = "logs/signal_debug.log"

def log_debug_signal(message: str):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

def update_entry_cache(symbol: str, price: float, direction: str) -> None:
    ENTRY_CACHE[symbol] = {
        "price": price,
        "ts": time.time(),
        "direction": direction,
    }

def allow_reentry(symbol: str, current_price: float, direction: str) -> bool:
    cached = ENTRY_CACHE.get(symbol)
    if not cached:
        return True
    if time.time() - cached.get("ts", 0) > ENTRY_TIMEOUT:
        return True
    if cached.get("direction") != direction:
        return True
    last_price = cached.get("price", 0)
    if abs(current_price - last_price) / max(last_price, 1) >= 0.01:
        return True
    return False

async def run_smc_strategy(symbol: str, capital: float = 1000, stop_event=None):
    try:
        if monitoring_only_mode or (stop_event and stop_event.is_set()) or await risk_limits_exceeded():
            log_debug_signal(f"{symbol}: стратегия пропущена — режим мониторинга или лимиты риска")
            return None

        df_raw = await get_ohlcv(symbol=symbol, interval="1h", limit=150)
        if not df_raw:
            log_debug_signal(f"{symbol}: нет данных OHLCV")
            return None

        df = pd.DataFrame(df_raw)
        if df.empty or len(df) < 100:
            log_debug_signal(f"{symbol}: недостаточно данных — {len(df)} свечей")
            return None

        ms = detect_market_structure(df)
        if not ms or ms.get("event") not in ["BOS", "CHOCH"]:
            log_debug_signal(f"{symbol}: структура рынка отсутствует или невалидный event")
            return None

        current_price = df["close"].iloc[-1]
        direction = determine_direction(ms["trend"])

        if direction == "neutral":
            log_debug_signal(f"{symbol}: тренд нейтральный — вход пропущен")
            return None

        if not allow_reentry(symbol, current_price, direction):
            log_debug_signal(f"{symbol}: повторный вход заблокирован")
            return None

        confidence = 0
        reasons = []

        if ms.get("event") == "BOS":
            confidence += CONFIDENCE_WEIGHTS.get("bos", 30)
            reasons.append("✅ BOS")

        if check_volume_spike(df):
            confidence += CONFIDENCE_WEIGHTS.get("volume_spike", 8)
            reasons.append("✅ Всплеск объёма")

        for liq in recent_liquidations:
            if liq["symbol"] == symbol and time.time() - liq.get("timestamp", 0) < 300:
                volume = liq.get("size", 0)
                confidence += 20 if volume > 100000 else 10
                reasons.append(f"💥 Ликвидация {volume}$")

        required_threshold = 40
        if confidence < required_threshold:
            log_debug_signal(f"{symbol}: confidence={confidence} < {required_threshold}, причины: {reasons}")
            return None

        sltp = get_dynamic_sl_tp(confidence, current_price, direction)
        if not sltp:
            log_debug_signal(f"{symbol}: ошибка расчёта SL/TP")
            return None

        risk_manager.set_equity(capital)
        size = risk_manager.calculate_position_size(
            balance=capital,
            entry=current_price,
            stop=sltp["sl"],
            confidence_score=confidence / 100
        )

        if not size or size <= 0:
            log_debug_signal(f"{symbol}: расчёт позиции дал 0")
            return None

        if not risk_manager.allowed_to_trade():
            log_debug_signal(f"{symbol}: торговля запрещена RiskManager")
            return None

        side = "buy" if direction == "long" else "sell"
        update_entry_cache(symbol, current_price, direction)

        success = await place_order(
            symbol=symbol,
            side=side,
            size=size,
            sl=sltp["sl"],
            tp2=sltp["tp2"]
        )

        if success:
            log_debug_signal(f"{symbol}: ордер размещён: size={size}, SL={sltp['sl']}, TP={sltp['tp2']}")
        else:
            log_debug_signal(f"{symbol}: ❌ ошибка размещения ордера")

    except Exception as e:
        logger.exception(f"❌ Ошибка стратегии SMC для {symbol}: {e}")
        log_debug_signal(f"{symbol}: исключение — {str(e)}")
        return None
