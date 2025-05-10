import threading

strategy_thread = None
is_running = False
strategy_stop_event = threading.Event()

# Новый флаг для отключения торговли при рисках
TRADING_DISABLED = False
