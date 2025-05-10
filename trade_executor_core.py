import asyncio
import os
from typing import Optional, Literal, Union

import ccxt.async_support as ccxt
from dotenv import load_dotenv

from core.state import TRADING_DISABLED
from log_setup import logger
from telegram_bot.position_alerts import notify_manual_close, notify_take_profit
from trade_journal import log_trade
from utils.telegram_utils import send_telegram_message
from position_manager.advanced_risk_manager import AdvancedRiskManager  # 💡 новый RiskManager

load_dotenv()

exchange: Optional[ccxt.Exchange] = None
risk_manager = AdvancedRiskManager()

# === Exchange Logic ===

async def init_exchange():
    global exchange
    exchange = ccxt.bybit({
        "apiKey": os.getenv("BYBIT_API_KEY") or "",
        "secret": os.getenv("BYBIT_API_SECRET") or "",
        "enableRateLimit": True,
        "options": {"defaultType": "future"},
    })
    await exchange.load_markets()

async def reconnect_exchange():
    global exchange
    try:
        if exchange is not None:
            await exchange.close()
            logger.info("🔁 Старое соединение с Bybit закрыто.")
    except Exception as e:
        logger.warning(f"⚠️ Ошибка при закрытии exchange: {e}")
    finally:
        await init_exchange()
        logger.info("✅ Переподключение к бирже завершено.")

async def get_exchange() -> ccxt.Exchange:
    global exchange
    if exchange is None:
        await init_exchange()
    if exchange is None:
        raise RuntimeError("❌ exchange не инициализирован")
    return exchange

def to_float(val: Union[str, float, int, None]) -> float:
    try:
        return float(val) if val is not None else 0.0
    except (ValueError, TypeError):
        return 0.0

# === Order Execution Logic ===

async def place_market_order(symbol: str, side: Literal["buy", "sell"], qty: float):
    if not risk_manager.allowed_to_trade():
        logger.warning(f"⛔ Отклонено открытие сделки {symbol} {side}: превышен риск-лимит.")
        return None
    logger.info(f"🔄 Маркет ордер: {side.upper()} {symbol}, qty={qty}")
    ex = await get_exchange()
    return await ex.create_order(symbol=symbol, type="market", side=side, amount=qty, params={"category": "linear"})

async def place_take_profit_order(symbol: str, side: Literal["buy", "sell"], price: float, qty: float):
    tp_side = "sell" if side == "buy" else "buy"
    logger.info(f"🎯 TP ордер ({tp_side.upper()}) {symbol}, price={price}, qty={qty}")
    ex = await get_exchange()
    return await ex.create_order(symbol=symbol, type="market", side=tp_side,
                                 amount=qty, params={"stopPrice": price, "reduceOnly": True, "category": "linear"})

async def place_stop_loss_order(symbol: str, side: Literal["buy", "sell"], price: float, qty: float):
    sl_side = "sell" if side == "buy" else "buy"
    logger.info(f"🛑 SL ордер ({sl_side.upper()}) {symbol}, price={price}, qty={qty}")
    ex = await get_exchange()
    return await ex.create_order(symbol=symbol, type="market", side=sl_side,
                                 amount=qty, params={"stopPrice": price, "reduceOnly": True, "category": "linear"})

async def get_open_position(symbol: str) -> Optional[dict]:
    try:
        ex = await get_exchange()
        positions = await ex.fetch_positions(symbols=[symbol], params={"category": "linear"})
        for p in positions or []:
            if p.get("symbol") == symbol:
                return {
                    "size": to_float(p.get("contracts")),
                    "side": (p.get("side") or "").lower(),
                    "entry": to_float(p.get("entryPrice")),
                }
    except Exception as e:
        logger.error(f"Ошибка получения позиции по {symbol}: {e}")
    return None

async def close_position(symbol: str) -> bool:
    if TRADING_DISABLED:
        logger.warning(f"⛔ Торговля отключена! Закрытие позиции по {symbol} отменено.")
        return False
    try:
        position = await get_open_position(symbol)
        if not position or position["size"] == 0:
            return True
        ex = await get_exchange()
        close_side = "sell" if position["side"] == "buy" else "buy"
        ticker = await ex.fetch_ticker(symbol)
        exit_price = to_float(ticker.get("last"))
        result = await ex.create_order(symbol=symbol, type="market", side=close_side,
                                       amount=position["size"], params={"reduceOnly": True, "category": "linear"})
        if not result:
            await send_telegram_message(f"❌ Не удалось закрыть позицию по {symbol}, все попытки неудачны.")
            return False

        logger.info(f"🚪 Позиция по {symbol} закрыта.")
        await notify_manual_close(symbol)

        pnl = (exit_price - position["entry"]) * position["size"] * (1 if position["side"] == "buy" else -1)
        log_trade(symbol, position["side"], position["size"], position["entry"], exit_price, pnl, "manual")
        return True
    except Exception as e:
        logger.error(f"Ошибка при закрытии позиции {symbol}: {e}")
        return False

async def market_close_partial(symbol: str, qty: float) -> bool:
    if TRADING_DISABLED:
        logger.warning(f"⛔ Торговля отключена! Частичное закрытие по {symbol} отменено.")
        return False
    try:
        position = await get_open_position(symbol)
        if not position or position["size"] == 0:
            return False
        ex = await get_exchange()
        close_side = "sell" if position["side"] == "buy" else "buy"
        ticker = await ex.fetch_ticker(symbol)
        exit_price = to_float(ticker.get("last"))
        result = await ex.create_order(symbol=symbol, type="market", side=close_side,
                                       amount=qty, params={"reduceOnly": True, "category": "linear"})
        if not result:
            await send_telegram_message(f"❌ Не удалось частично закрыть {symbol}, все попытки неудачны.")
            return False

        logger.info(f"💰 Частично закрыта позиция по {symbol}, qty={qty}")
        await notify_take_profit(symbol, qty, exit_price)

        pnl = (exit_price - position["entry"]) * qty * (1 if position["side"] == "buy" else -1)
        log_trade(symbol, position["side"], qty, position["entry"], exit_price, pnl, "tp")
        return True
    except Exception as e:
        logger.error(f"Ошибка при частичном закрытии {symbol}: {e}")
        return False

async def update_stop_loss(symbol: str, new_sl: float) -> None:
    logger.info(f"🔄 Обновление SL по {symbol} до {new_sl}. (Не реализовано)")

async def place_order(
    symbol: str,
    side: Literal["buy", "sell"],
    size: float,
    sl: float,
    tp2: float,
    tp1: Optional[float] = None,
    tp1_ratio: float = 0.5
) -> bool:
    if TRADING_DISABLED:
        logger.warning(f"⛔ Торговля отключена! Открытие позиции по {symbol} отменено.")
        return False
    try:
        if not risk_manager.allowed_to_trade():
            logger.warning(f"⛔ Отклонено открытие сделки по {symbol}: лимит дневных убытков достигнут.")
            return False

        position = await get_open_position(symbol)
        if position and position["size"] > 0:
            logger.warning(f"🔄 Уже открыта позиция по {symbol}. Сначала закрываем её.")
            await close_position(symbol)
            await asyncio.sleep(2)

        result = await place_market_order(symbol, side, size)
        if not result:
            await send_telegram_message(f"❌ Не удалось открыть позицию по {symbol}, все попытки неудачны.")
            return False

        if tp1 and tp2 and 0 < tp1_ratio < 1:
            tp1_qty = round(size * tp1_ratio, 3)
            tp2_qty = round(size - tp1_qty, 3)
            await place_take_profit_order(symbol, side, tp1, tp1_qty)
            await place_take_profit_order(symbol, side, tp2, tp2_qty)
            logger.info(f"📌 Установлены TP1: {tp1} ({tp1_qty}), TP2: {tp2} ({tp2_qty})")
        else:
            await place_take_profit_order(symbol, side, tp2, size)
            logger.info(f"📌 Установлен TP2: {tp2} на весь объём")

        await place_stop_loss_order(symbol, side, sl, size)
        logger.info(f"📌 Установлен SL: {sl}")

        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при выставлении ордеров: {e}")
        return False
