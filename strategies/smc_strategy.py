import json
import time
import pandas as pd
import os

from api.bybit_async import get_ohlcv
from indicators.market_structure import detect_market_structure
from log_setup import logger
from monitor_liquidations import monitoring_only_mode
from utils.direction import determine_direction
from utils.dynamic_sl_tp import get_dynamic_sl_tp_advanced
from utils.liquidation_ws import recent_liquidations
from utils.risk_limits import risk_limits_exceeded
from utils.volume import check_volume_spike
from trade_executor_core import place_order, risk_manager
from utils.log_signal import log_signal
from typing import Literal

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

def normalize_confidence(raw_confidence: float) -> float:
    max_weight_sum = sum(CONFIDENCE_WEIGHTS.values()) or 100
    return min(raw_confidence / max_weight_sum, 1.0)

async def run_smc_strategy(symbol: str, capital: float = 1000, stop_event=None, default_risk_pct: float = 0.01, leverage: float = 5.0):
    print("🔥 старт run_smc_strategy")
    try:
        if os.path.exists("halt.flag"):
            log_debug_signal(f"{symbol}: стратегия остановлена — обнаружен halt.flag")
            return None

        if os.path.exists("pause.flag"):
            log_debug_signal(f"{symbol}: стратегия приостановлена — активен pause.flag")
            return None

        if monitoring_only_mode or (stop_event and stop_event.is_set()) or await risk_limits_exceeded():
            log_debug_signal(f"{symbol}: стратегия пропущена — режим мониторинга или лимиты риска")
            return None

        df_raw = await get_ohlcv(symbol=symbol, interval="60", limit=150)
        if not df_raw:
            log_debug_signal(f"{symbol}: нет данных OHLCV")
            return None

        df = pd.DataFrame(df_raw)
        print(f"✅ Получено {len(df)} свечей для {symbol}")

        if df.empty or len(df) < 100:
            log_debug_signal(f"{symbol}: недостаточно данных — {len(df)} свечей")
            return None

        ms = detect_market_structure(df)
        print(f"✅ Market structure: {ms}")

        if not ms or ms.get("event") not in ["BOS", "CHOCH"]:
            log_debug_signal(f"{symbol}: структура рынка отсутствует или невалидный event")
            return None

        current_price = df["close"].iloc[-1]
        direction = determine_direction(ms["trend"])
        print(f"✅ Направление тренда: {direction}")

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

        normalized_conf = normalize_confidence(confidence)
        print(f"✅ Confidence: {confidence}, normalized: {normalized_conf}")
        print(f"✅ Причины входа: {reasons}")

        sl_tp = get_dynamic_sl_tp_advanced(df, current_price, direction, normalized_conf, symbol)

        side: Literal["buy", "sell"] = "buy" if direction == "long" else "sell"

        size = risk_manager.calculate_position_size(
            balance=capital,
            entry=current_price,
            stop=sl_tp["sl"],
            confidence_score=normalized_conf,
            leverage=leverage
        )
        print(f"✅ Размер позиции: {size}")

        if size == 0:
            log_debug_signal(f"{symbol}: size == 0 — риск менеджмент отклонил вход")
            return None

        await place_order(
            symbol=symbol,
            side=side,
            size=size,
            sl=sl_tp["sl"],
            tp2=sl_tp["tp2"],
            tp1=sl_tp.get("tp1"),
            tp1_ratio=sl_tp.get("tp1_ratio", 0.0)
        )
        update_entry_cache(symbol, current_price, direction)

        log_signal(
            symbol=symbol,
            direction=direction,
            price=current_price,
            sl=sl_tp["sl"],
            tp=sl_tp["tp2"],
            size=size,
            confidence=confidence,
            reasons=reasons,
            status="live",
            result="pending",
            pnl=0.0
        )

    except Exception as e:
        log_debug_signal(f"❌ Ошибка run_smc_strategy({symbol}): {str(e)}")
        return None
