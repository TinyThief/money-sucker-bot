import asyncio
from collections.abc import Callable
from typing import Any

import ccxt

from trade_executor_core import reconnect_exchange
from log_setup import logger


async def safe_execute(
    fn: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> Any | None:
    """Безопасно выполняет функцию с переподключением."""
    try:
        if asyncio.iscoroutinefunction(fn):
            return await fn(*args, **kwargs)
        return fn(*args, **kwargs)

    except (ccxt.NetworkError, ccxt.ExchangeNotAvailable, ccxt.RequestTimeout) as e:
        logger.warning("🌐 Сетевая ошибка в %s: %s. Переподключаемся...", fn.__name__, str(e))
        await reconnect_exchange()  # <-- ВАЖНО: добавлен await
        await asyncio.sleep(2)

        try:
            if asyncio.iscoroutinefunction(fn):
                return await fn(*args, **kwargs)
            return fn(*args, **kwargs)
        except (ccxt.BaseError, RuntimeError) as e2:
            logger.error("❌ Ошибка после переподключения в %s: %s", fn.__name__, str(e2))
            return None

    except (ValueError, RuntimeError) as e:
        logger.error("❌ Ошибка в safe_execute (%s): %s", fn.__name__, str(e))
        return None
