import asyncio

from api.bybit_async import fetch_balance as get_balance
from core.state import strategy_stop_event
from event_driven_heartbeat import last_known_status, send_event_heartbeat  # ✅ Подключаем!
from log_setup import logger
from strategies.smc_strategy import run_smc_strategy
from utils.load_tickers import load_tickers
from utils.telegram_utils import send_telegram_message

FAIL_LIMIT = 3
CHECK_INTERVAL_SECONDS = 60
sp_sleep = False  # Флаг спящего режима

async def monitor_connection_status() -> None:
    global sp_sleep
    fail_count = 0
    alerted = False

    while True:
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
        try:
            usdt, free, used = get_balance()
            if usdt is not None:
                if alerted:
                    logger.info("✅ Связь с биржей восстановлена.")
                    await send_telegram_message("✅ Связь с биржей восстановлена. Пытаемся вернуться в работу.")

                    if sp_sleep:
                        logger.info("♻️ Выход из спящего режима, перезапуск стратегий...")
                        await restart_strategies()
                        sp_sleep = False

                fail_count = 0
                alerted = False

                # Проверяем изменение статуса соединения
                if last_known_status["connection_ok"] is False:
                    await send_event_heartbeat("✅ Связь с биржей восстановлена")
                    last_known_status["connection_ok"] = True

            else:
                fail_count += 1
                logger.warning(f"⚠️ Ошибка получения баланса. Ошибок подряд: {fail_count}")

        except Exception as e:
            logger.error(f"❌ Ошибка проверки связи с биржей: {e}")
            fail_count += 1

        if fail_count >= FAIL_LIMIT and not alerted:
            logger.error("🚨 Связь с биржей потеряна!")
            await send_telegram_message("🚨 ВНИМАНИЕ: Потеряна связь с биржей! Переход в спящий режим...")
            alerted = True
            sp_sleep = True
            strategy_stop_event.set()

            # Отправляем event-driven heartbeat
            if last_known_status["connection_ok"] is not False:
                await send_event_heartbeat("🚨 Связь с биржей потеряна")
                last_known_status["connection_ok"] = False

async def restart_strategies() -> None:
    try:
        tickers = await load_tickers()

        for symbol in tickers:
            asyncio.create_task(run_smc_strategy(
                symbol=symbol,
                capital=1000,
                default_risk_pct=0.01,
            ))

        await send_telegram_message("✅ Стратегии успешно перезапущены!")
        strategy_stop_event.clear()

    except Exception as e:
        logger.error(f"Ошибка при автоперезапуске стратегий после восстановления: {e}")
        await send_telegram_message("❌ Ошибка при автоперезапуске стратегий после восстановления.")
