import asyncio
import json
import time
from collections import deque

import websockets

from api.bybit_async import set_leverage
from log_setup import logger
from utils.telegram_utils import send_telegram_message

# --- Константы
LIQUIDATION_THRESHOLD_USDT = 50000
BYBIT_WSS_URL = "wss://stream.bybit.com/v5/public/linear"

# --- Глобальные переменные
liquidation_counter = 0
current_risk_pct = 0.01
current_rr = 2.0
monitoring_only_mode = False
emergency_active = False

recent_liquidations = deque(maxlen=100)

HIGH_VOLATILITY_THRESHOLD = 0.015
LOW_VOLATILITY_THRESHOLD = 0.007

# --- Основная функция мониторинга ликвидаций
async def monitor_liquidations() -> None:
    global liquidation_counter, current_risk_pct, current_rr, monitoring_only_mode

    while True:
        try:
            async with websockets.connect(BYBIT_WSS_URL) as ws:
                logger.info("🧩 WebSocket ликвидаций Bybit подключён.")

                subscribe_message = {
                    "op": "subscribe",
                    "args": ["liquidation.*"],
                }
                await ws.send(json.dumps(subscribe_message))

                async for message in ws:
                    await handle_liquidation_message(message)

        except Exception as e:
            logger.error(f"Ошибка WebSocket ликвидаций: {e}")
            await asyncio.sleep(10)

# --- Обработка входящего сообщения ликвидаций
async def handle_liquidation_message(message) -> None:
    global liquidation_counter

    try:
        data = json.loads(message)
        if "data" in data:
            for item in data["data"]:
                size = float(item.get("qty", 0))
                price = float(item.get("price", 0))
                side = item.get("side", "Unknown")
                symbol = item.get("symbol", "Unknown")

                liquidation_value = size * price

                if liquidation_value >= LIQUIDATION_THRESHOLD_USDT:
                    msg = (
                        f"💥 Крупная ликвидация на {symbol}!\n"
                        f"• Направление: {side}\n"
                        f"• Размер ликвидации: {liquidation_value:.2f} USDT\n"
                        f"• Цена: {price:.2f} USDT"
                    )
                    logger.warning(msg)
                    await send_telegram_message(msg)

                    recent_liquidations.append({
                        "symbol": symbol,
                        "side": side,
                        "price": price,
                        "qty": size,
                        "value": liquidation_value,
                        "timestamp": time.time(),
                    })

                    liquidation_counter += 1
                    await check_and_update_risk()
                    await check_emergency_conditions()

    except Exception as e:
        logger.error(f"Ошибка обработки ликвидации: {e}")

# --- Проверка количества ликвидаций и адаптация риска
async def check_and_update_risk() -> None:
    global liquidation_counter, current_risk_pct, current_rr, monitoring_only_mode

    if liquidation_counter >= 20:
        current_risk_pct = 0.003
        current_rr = 1.2
        monitoring_only_mode = True
        liquidation_counter = 0
        await send_telegram_message("🚨 Сильнейшая волатильность! Переход в Monitoring-Only Mode!")

    elif liquidation_counter < 3:
        current_risk_pct = 0.015
        current_rr = 3.0
        monitoring_only_mode = False
        liquidation_counter = 0
        await send_telegram_message("🌙 Рынок стабилен. Возвращаем торговлю в нормальный режим.")

    else:
        current_risk_pct = 0.01
        current_rr = 2.0
        monitoring_only_mode = False

# --- Проверка условий для Emergency Stop
async def check_emergency_conditions() -> None:
    if count_recent_liquidations(300, 500000) >= 5:
        await activate_emergency_stop(reason="Массовые ликвидации за 5 минут")

def count_recent_liquidations(time_window_sec: int, min_value_usdt: float) -> int:
    now = time.time()
    return sum(1 for liq in recent_liquidations if now - liq.get("timestamp", 0) <= time_window_sec and liq.get("value", 0) >= min_value_usdt)

async def activate_emergency_stop(reason: str) -> None:
    global emergency_active
    if not emergency_active:
        emergency_active = True
        logger.error(f"🚨 Emergency Stop активирован: {reason}")
        await send_telegram_message(f"🚨 Emergency Stop активирован: {reason}")

# --- Управление адаптивным плечом
async def adjust_leverage(symbol: str, atr_value: float) -> None:
    try:
        if atr_value > HIGH_VOLATILITY_THRESHOLD:
            leverage = 2
        elif atr_value < LOW_VOLATILITY_THRESHOLD:
            leverage = 4
        else:
            leverage = 3

        await set_leverage(symbol, leverage)
        logger.info(f"⚙️ Плечо для {symbol} установлено: {leverage}x")
        await send_telegram_message(f"⚙️ Плечо для <b>{symbol}</b> установлено: {leverage}x")
    except Exception as e:
        logger.error(f"❌ Ошибка изменения плеча: {e}")
