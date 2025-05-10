import time

from config.variables import LOSS_LIMIT_COUNT, LOSS_LIMIT_USDT, RISK_RESET_INTERVAL
from log_setup import logger
from utils.telegram_utils import send_telegram_message

# --- Состояние торговли ---
TRADING_DISABLED = False

# --- Состояние количества сделок ---
TRADE_COUNTER = {
    "count": 0,
}

# --- Максимальное зафиксированное equity для drawdown расчёта ---
LAST_EQUITY = {
    "max": 1000.0,
}

# --- Глобальное состояние риска ---
RISK_STATE = {
    "loss_count": 0,
    "total_loss": 0.0,
    "last_reset": time.time(),
}

# --- Параметры лимитов ---
MAX_DRAWDOWN_PCT = 0.5
MAX_TRADES_PER_SESSION = 5

def get_equity() -> float:
    """Псевдо-функция получения текущего капитала (можно заменить на API)."""
    return 1000.0


async def update_risk(pnl: float) -> None:
    """Обновляет состояние рисков. PnL может быть отрицательным или положительным."""
    now = time.time()

    if now - RISK_STATE["last_reset"] > RISK_RESET_INTERVAL:
        logger.info("🔁 Сброс лимитов риска по интервалу времени.")
        RISK_STATE["loss_count"] = 0
        RISK_STATE["total_loss"] = 0.0
        TRADE_COUNTER["count"] = 0
        RISK_STATE["last_reset"] = now

    if pnl < 0:
        RISK_STATE["loss_count"] += 1
        RISK_STATE["total_loss"] += abs(pnl)
    else:
        RISK_STATE["loss_count"] = 0
        RISK_STATE["total_loss"] = max(0.0, RISK_STATE["total_loss"] - pnl)

    TRADE_COUNTER["count"] += 1


async def risk_limits_exceeded() -> bool:
    """Проверяет, превышены ли лимиты риска."""
    global TRADING_DISABLED

    equity = get_equity()
    max_equity = LAST_EQUITY["max"]
    drawdown_pct = (max_equity - equity) / max_equity if max_equity > 0 else 0

    if drawdown_pct >= MAX_DRAWDOWN_PCT:
        logger.warning("⛔ Превышен лимит просадки.")
        await safe_send_telegram("⚠️ Бот остановлен: лимит просадки.")
        TRADING_DISABLED = True
        return True

    if TRADE_COUNTER["count"] > MAX_TRADES_PER_SESSION:
        logger.warning("⛔ Превышено количество сделок.")
        await safe_send_telegram("⚠️ Бот остановлен: лимит количества сделок.")
        TRADING_DISABLED = True
        return True

    if RISK_STATE["loss_count"] >= LOSS_LIMIT_COUNT:
        logger.warning("⛔ Превышен лимит подряд убытков.")
        await safe_send_telegram("⚠️ Бот остановлен: лимит подряд убытков.")
        TRADING_DISABLED = True
        return True

    if RISK_STATE["total_loss"] >= LOSS_LIMIT_USDT:
        logger.warning("⛔ Превышен лимит суммарного убытка.")
        await safe_send_telegram("⚠️ Бот остановлен: лимит по суммарному убытку.")
        TRADING_DISABLED = True
        return True

    return False


async def safe_send_telegram(message: str) -> None:
    """Безопасная отправка уведомления в Telegram без риска краша."""
    try:
        await send_telegram_message(message)
    except Exception as e:
        logger.error(f"❌ Ошибка отправки Telegram уведомления: {e}")