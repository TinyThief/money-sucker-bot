import asyncio

from api.bybit_async import get_open_positions
from log_setup import logger
from position_manager.monitor_positions import monitor_single_position  # правильный импорт

monitored_symbols = set()

async def monitor_all_positions_loop() -> None:
    logger.info("🚦 Запущен мониторинг всех открытых позиций...")

    while True:
        try:
            positions = await get_open_positions()  # ✅ await
            for p in positions:
                symbol = p["symbol"]
                if symbol not in monitored_symbols and p["size"] > 0:
                    logger.info(f"📡 Начинаем сопровождение позиции: {symbol}")

                    asyncio.create_task(monitor_single_position(
                        symbol=symbol,
                        tp1=p.get("tp1"),
                        tp2=p.get("tp2"),
                        entry=p.get("entry_price"),
                        direction=p.get("side"),
                        stop_loss=p.get("stop_loss"),
                    ))

                    monitored_symbols.add(symbol)

        except Exception as e:
            logger.error(f"❌ Ошибка при мониторинге позиций: {e}")

        await asyncio.sleep(10)
