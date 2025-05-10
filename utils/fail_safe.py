from log_setup import logger


def safe_execute(fn, *args, **kwargs):
    """Универсальный безопасный вызов функции с логированием ошибки."""
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        logger.error(f"❌ Ошибка в safe_execute ({fn.__name__}): {e}")
        return None
