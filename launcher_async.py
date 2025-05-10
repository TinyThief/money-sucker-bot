import asyncio
import time
import nest_asyncio

from api.bybit_async import fetch_balance, get_exchange, get_ohlcv, get_current_leverage, set_leverage
from heartbeat_task import start_heartbeat
from log_setup import logger
from monitor_balance_status import monitor_balance_status
from monitor_connection_status import monitor_connection_status
from monitor_liquidations import monitor_liquidations
from position_manager.monitor_positions import monitor_all_positions
from strategies.smc_strategy import run_smc_strategy
from telegram_bot.bot_main import start_telegram
from telegram_bot.monitor_strategies_status import monitor_strategies_status
from tools.daily_performance_checker import daily_performance_check
from trade_executor_core import place_order, risk_manager, init_exchange
from utils.telegram_utils import send_telegram_message
from backtest.optimize_confidence import scheduler

cooldown_active = False
cooldown_until = None
loss_streak = 0
LOSS_STREAK_LIMIT = 3
COOLDOWN_DURATION_MINUTES = 120

async def fetch_bybit_symbols():
    ex = await get_exchange()
    markets = await ex.load_markets()
    return [
        symbol for symbol in markets
        if symbol.endswith("USDT") and ":USDT" not in symbol and markets[symbol]["active"]
    ]

async def filter_top_symbols(symbols, top_n=10):
    scored = []
    for symbol in symbols:
        try:
            df = await get_ohlcv(symbol, interval="1h", limit=50)
            if df:
                closes = [c["close"] for c in df]
                volumes = [c["volume"] for c in df]
                volatility = max(closes) / min(closes) - 1
                volume = sum(volumes)
                score = volatility * volume
                scored.append((symbol, score))
        except:
            continue
    scored.sort(key=lambda x: x[1], reverse=True)
    return [s[0] for s in scored[:top_n]]

def calculate_atr_percent(price: float, atr_value: float) -> float:
    if price == 0:
        return 0
    return atr_value / price

async def periodic_performance_check():
    while True:
        await daily_performance_check()
        await asyncio.sleep(86400)

async def adjust_leverage_safe(symbol: str, atr_percent: float | None):
    try:
        if atr_percent is None:
            logger.warning(f"⚠️ atr_percent is None для {symbol}, пропуск установки плеча")
            return
        current_lev = await get_current_leverage(symbol)
        target_lev = 3 if atr_percent < 0.03 else 2
        if current_lev != target_lev:
            await set_leverage(symbol, target_lev)
            logger.info(f"[BybitAsync] Установлено плечо {target_lev}x для {symbol}")
    except Exception as e:
        logger.error(f"❌ Ошибка изменения плеча: {e}")

async def strategy_worker(symbol: str):
    global cooldown_active, cooldown_until, loss_streak
    try:
        while True:
            now = time.time()
            if cooldown_active and cooldown_until and now < cooldown_until:
                logger.info(f"🛑 Cooldown активен. Пропуск сигналов для {symbol}")
                await asyncio.sleep(60)
                continue
            if cooldown_active and cooldown_until and now >= cooldown_until:
                cooldown_active = False
                loss_streak = 0
                await send_telegram_message("✅ Cooldown окончен. Торговля возобновлена.")

            capital = 1000
            balance = await fetch_balance()
            if balance is None:
                logger.warning(f"⚠️ Не удалось получить баланс, пропуск {symbol}")
                await asyncio.sleep(30)
                continue

            risk_manager.set_equity(balance)
            signal = await run_smc_strategy(symbol=symbol, capital=capital)
            if signal:
                entry = signal.get("entry_price")
                if not isinstance(entry, (float, int)) or entry <= 0:
                    logger.warning(f"⚠️ Недопустимая цена входа {entry} для {symbol}, пропуск сигнала.")
                    await asyncio.sleep(30)
                    continue

                if risk_manager.allowed_to_trade():
                    atr_value = 0.01 * entry
                    atr_percent = calculate_atr_percent(entry, atr_value)
                    symbol_fixed = signal["symbol"].replace("/", "")
                    await adjust_leverage_safe(symbol_fixed, atr_percent)
                    size = risk_manager.calculate_position_size(balance, entry, signal["stop_loss"], signal["confidence"] / 100)
                    if size is None or size <= 0:
                        logger.error(f"[{symbol}] Ошибка расчета размера позиции: size={size}")
                        await asyncio.sleep(30)
                        continue

                    result = await place_order(
                        symbol=signal["symbol"],
                        side=signal["direction"].lower(),
                        size=size,
                        sl=signal["stop_loss"],
                        tp2=signal["take_profit"],
                    )
                    if result is False:
                        loss_streak += 1
                        if loss_streak >= LOSS_STREAK_LIMIT:
                            cooldown_active = True
                            cooldown_until = now + (COOLDOWN_DURATION_MINUTES * 60)
                            await send_telegram_message("🚨 Активирован режим Auto-Cooldown на 2 часа!")
            await asyncio.sleep(30 if not cooldown_active else 90)
    except Exception as e:
        logger.error(f"❌ Ошибка в worker {symbol}: {e}")

async def launch_background_tasks():
    await asyncio.gather(
        start_heartbeat(),
        monitor_all_positions(),
        monitor_strategies_status(),
        monitor_connection_status(),
        monitor_balance_status(),
        monitor_liquidations(),
        periodic_performance_check(),
    )

async def start_full():
    nest_asyncio.apply()
    scheduler.start()
    await start_telegram()

async def main():
    logger.info("🚀 Async launcher с автоанализом пар запущен!")
    await init_exchange()
    await asyncio.gather(
        launch_background_tasks(),
        start_full()
    )
    all_symbols = await fetch_bybit_symbols()
    tickers = await filter_top_symbols(all_symbols, top_n=10)
    logger.info(f"📈 Выбраны топ-пары: {tickers}")
    strategy_tasks = [asyncio.create_task(strategy_worker(symbol)) for symbol in tickers]
    await asyncio.gather(*strategy_tasks)

if __name__ == "__main__":
    import sys
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    while True:
        try:
            asyncio.run(main())
        except Exception:
            logger.exception("❌ Фатальная ошибка в launcher_async. Перезапуск через 30 секунд...")
            try:
                asyncio.run(send_telegram_message("❌ Бот упал с ошибкой! Перезапуск через 30 секунд..."))
            except Exception:
                logger.warning("⚠️ Не удалось отправить сообщение о падении.")
            time.sleep(30)
            logger.info("🔄 Попытка перезапуска бота...")
