import logging
import json
import hmac
import hashlib
import os
import time
import aiohttp

from dotenv import load_dotenv
from trade_executor_core import get_exchange

load_dotenv()

logger = logging.getLogger("BybitAsync")
logger.setLevel(logging.INFO)

api_key = os.getenv("BYBIT_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET")
if not api_secret:
    raise ValueError("Environment variable BYBIT_API_SECRET is not set.")
assert isinstance(api_secret, str), "api_secret must be a string."

BASE_URL = "https://api.bybit.com"
RECV_WINDOW = "5000"


def get_timestamp() -> str:
    return str(int(time.time() * 1000))


def create_signature(payload: str) -> str:
    return hmac.new(
        bytes(api_secret or "", "utf-8"), bytes(payload, "utf-8"), hashlib.sha256
    ).hexdigest()


def get_auth_headers(payload: str, timestamp: str) -> dict:
    return {
        "X-BAPI-API-KEY": api_key,
        "X-BAPI-SIGN": create_signature(payload),
        "X-BAPI-TIMESTAMP": timestamp,
        "X-BAPI-RECV-WINDOW": RECV_WINDOW,
        "Content-Type": "application/json",
    }


async def set_leverage(symbol: str, leverage: int):
    endpoint = "/v5/position/set-leverage"
    url = BASE_URL + endpoint
    symbol = symbol.replace("/", "")

    params = {
        "symbol": symbol,
        "buyLeverage": str(leverage),
        "sellLeverage": str(leverage),
        "category": "linear",
    }

    timestamp = get_timestamp()
    params_json = json.dumps(params, separators=(",", ":"))
    sign_payload = f"{timestamp}{api_key}{RECV_WINDOW}{params_json}"
    headers = get_auth_headers(sign_payload, timestamp)

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=params_json) as resp:
            try:
                data = await resp.json()
            except Exception as e:
                logger.error(
                    f"[BybitAsync] ❌ Ошибка чтения JSON ответа set_leverage: {e}"
                )
                raise

            if not data or data.get("retCode") != 0:
                logger.error(f"[BybitAsync] Ошибка установки плеча: {data}")
                raise Exception(f"Ошибка установки плеча: {data}")

            logger.info(f"[BybitAsync] Установлено плечо {leverage}x для {symbol}")
            return data


async def get_current_leverage(symbol: str) -> int | None:
    return 3


...


async def get_open_positions():
    endpoint = "/v5/position/list"
    url = BASE_URL + endpoint
    params = {"category": "linear"}

    timestamp = get_timestamp()
    params_json = json.dumps(params, separators=(",", ":"))
    sign_payload = f"{timestamp}{api_key}{RECV_WINDOW}{params_json}"
    headers = get_auth_headers(sign_payload, timestamp)

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, data=params_json) as resp:
                data = await resp.json()
        except Exception as e:
            logger.error(
                f"[BybitAsync] ❌ Ошибка чтения JSON ответа get_open_positions: {e}"
            )
            return []

    if not data or data.get("retCode") != 0:
        logger.error(f"[BybitAsync] Ошибка получения позиций: {data}")
        return []

    if not isinstance(data.get("result", {}).get("list"), list):
        logger.error(
            f"[BybitAsync] ❌ Неверный формат ответа get_open_positions: {data}"
        )
        return []

    raw_positions = data["result"].get("list", [])
    parsed_positions = []

    for pos in raw_positions:
        size = float(pos.get("size", 0))
        if size > 0:
            parsed_positions.append(
                {
                    "symbol": pos.get("symbol"),
                    "side": pos.get("side"),
                    "size": size,
                    "entry": float(pos.get("entryPrice", 0)),
                    "pnl": float(pos.get("unrealisedPnl", 0)),
                }
            )

    return parsed_positions


async def fetch_balance():
    try:
        ex = get_exchange()
        exchange = await ex
        balance_data = await exchange.fetch_balance()
        return (
            float(balance_data["total"].get("USDT", 0)),
            float(balance_data["free"].get("USDT", 0)),
            float(balance_data["used"].get("USDT", 0)),
        )
    except Exception as e:
        logger.exception(f"[BybitAsync] Ошибка получения баланса: {e}")
        return None


async def get_ohlcv(symbol: str, interval: str = "60", limit: int = 150):
    endpoint = "/v5/market/kline"
    url = BASE_URL + endpoint
    symbol = symbol.replace("/", "")

    params = {
        "category": "linear",
        "symbol": symbol,
        "interval": interval,
        "limit": limit,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                data = await resp.json()
    except Exception as e:
        logger.warning(f"[BybitAsync] ❌ Ошибка при получении OHLCV {symbol}: {e}")
        return []

    if not data or data.get("retCode") != 0:
        logger.warning(f"[BybitAsync] OHLCV ошибка: {json.dumps(data, indent=2)}")
        return []

    raw_klines = data.get("result", {}).get("list", [])
    if not raw_klines:
        logger.warning(f"[BybitAsync] ⚠️ Пустой OHLCV для {symbol}")
        return []

    return [
        {
            "timestamp": int(k[0]),
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
            "volume": float(k[5]),
        }
        for k in raw_klines
    ]


async def update_stop_loss(symbol: str, stop_loss_price: float):
    endpoint = "/v5/position/trading-stop"
    url = BASE_URL + endpoint
    symbol = symbol.replace("/", "")

    params = {"symbol": symbol, "stopLoss": str(stop_loss_price), "category": "linear"}

    timestamp = get_timestamp()
    params_json = json.dumps(params, separators=(",", ":"))
    sign_payload = f"{timestamp}{api_key}{RECV_WINDOW}{params_json}"
    headers = get_auth_headers(sign_payload, timestamp)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=params_json) as resp:
                data = await resp.json()
    except Exception as e:
        logger.error(f"[BybitAsync] ❌ Ошибка запроса update_stop_loss: {e}")
        return False

    if not data or data.get("retCode") != 0:
        logger.error(f"[BybitAsync] ❌ Ошибка обновления SL: {data}")
        return False

    logger.info(f"[BybitAsync] ✅ SL обновлён до {stop_loss_price} для {symbol}")
    return True


async def get_current_price(symbol: str) -> float | None:
    endpoint = "/v5/market/tickers"
    url = BASE_URL + endpoint
    symbol = symbol.replace("/", "")

    params = {"category": "linear", "symbol": symbol}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                data = await resp.json()
    except Exception as e:
        logger.error(f"[BybitAsync] ❌ Ошибка при получении цены {symbol}: {e}")
        return None

    if not data or data.get("retCode") != 0:
        logger.error(f"[BybitAsync] ❌ Ошибка получения цены: {data}")
        return None

    result = data.get("result", {}).get("list", [])
    if not result:
        logger.warning(f"[BybitAsync] ❗ Пустой ответ по цене для {symbol}")
        return None

    return float(result[0]["lastPrice"])


async def get_order_book(symbol: str) -> dict | None:
    endpoint = "/v5/market/deep"
    url = BASE_URL + endpoint
    symbol = symbol.replace("/", "")

    params = {"category": "linear", "symbol": symbol, "limit": 5}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                data = await resp.json()
    except Exception as e:
        logger.error(f"[BybitAsync] ❌ Ошибка при получении стакана {symbol}: {e}")
        return None

    if not data or data.get("retCode") != 0:
        logger.error(f"[BybitAsync] ❌ Ошибка получения стакана: {data}")
        return None

    result = data.get("result", {})
    if not result:
        logger.warning(f"[BybitAsync] ❗ Пустой ответ по стакану для {symbol}")
        return None

    return {
        "bids": [
            {"price": float(bid[0]), "size": float(bid[1])}
            for bid in result.get("bids", [])
        ],
        "asks": [
            {"price": float(ask[0]), "size": float(ask[1])}
            for ask in result.get("asks", [])
        ],
    }


async def get_open_orders(symbol: str):
    endpoint = "/v5/order/list"
    url = BASE_URL + endpoint
    symbol = symbol.replace("/", "")

    params = {"symbol": symbol, "orderStatus": "New", "category": "linear"}

    timestamp = get_timestamp()
    params_json = json.dumps(params, separators=(",", ":"))
    sign_payload = f"{timestamp}{api_key}{RECV_WINDOW}{params_json}"
    headers = get_auth_headers(sign_payload, timestamp)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=params_json) as resp:
                data = await resp.json()
    except Exception as e:
        logger.error(f"[BybitAsync] ❌ Ошибка получения открытых ордеров {symbol}: {e}")
        return []

    if not data or data.get("retCode") != 0:
        logger.error(f"[BybitAsync] ❌ Ошибка API при получении ордеров: {data}")
        return []

    orders = data.get("result", {}).get("list", [])
    return [
        {
            "order_id": o.get("orderId"),
            "symbol": o.get("symbol"),
            "price": float(o.get("price", 0)),
            "qty": float(o.get("qty", 0)),
            "side": o.get("side"),
            "order_type": o.get("orderType"),
            "created_time": int(o.get("createdTime", 0)),
        }
        for o in orders
    ]
