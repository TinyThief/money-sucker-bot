import asyncio

from core.state import strategy_stop_event
from event_driven_heartbeat import last_known_status, send_event_heartbeat  # ✅ Импортируем Event-Driven Heartbeat
from log_setup import logger
from strategies.smc_strategy import run_smc_strategy
from utils.load_tickers import load_tickers
from utils.telegram_utils import send_telegram_message
from config import settings  # ⬅️ Подключаем глобальные настройки

alert_sent: bool = False

async def monitor_strategies_status() -> None:
    global alert_sent

    while True:
        try:
            await asyncio.sleep(60)  # Проверяем раз в минуту

            # Сначала проверка изменения состояния стратегий для Heartbeat
            current_strategies_running = not strategy_stop_event.is_set()

            if "strategies_running" not in last_known_status or not isinstance(last_known_status["strategies_running"], bool):
                last_known_status["strategies_running"] = current_strategies_running

            if current_strategies_running != last_known_status["strategies_running"]:
                status_text = "✅ Стратегии запущены" if current_strategies_running else "⛔ Стратегии остановлены"
                await send_event_heartbeat(status_text)
                last_known_status["strategies_running"] = current_strategies_running

            # Проверка падения стратегий и попытка перезапуска
            if strategy_stop_event.is_set():
                if not alert_sent:
                    logger.warning("🚨 Стратегии остановлены! Отправка алерта в Telegram.")
                    await send_telegram_message("🚨 ВНИМАНИЕ: Стратегии остановились! Попытка перезапуска через 30 секунд...")
                    alert_sent = True

                    await asyncio.sleep(30)  # Пауза перед перезапуском

                    logger.info("♻️ Попытка перезапустить стратегии...")
                    await restart_strategies()
            else:
                alert_sent = False  # Если восстановились — сбрасываем флаг

        except Exception as e:
            logger.error(f"Ошибка в monitor_strategies_status: {e}")

async def restart_strategies() -> None:
    try:
        tickers = await load_tickers()

        for symbol in tickers:
            asyncio.create_task(run_smc_strategy(
                symbol=symbol,
                capital=1000,
                default_risk_pct=settings.DEFAULT_RISK_PCT,
            ))

        await send_telegram_message("✅ Стратегии успешно перезапущены!")

        # Сброс флага остановки
        strategy_stop_event.clear()

    except Exception as e:
        logger.error(f"Ошибка при автоперезапуске стратегий: {e}")
        await send_telegram_message("❌ Ошибка при автоперезапуске стратегий.")
