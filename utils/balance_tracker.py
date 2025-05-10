import csv
import os
from datetime import datetime

DATA_PATH = "data"
EQUITY_FILE = os.path.join(DATA_PATH, "equity_curve.csv")

# Создание директории и файла при первом запуске
os.makedirs(DATA_PATH, exist_ok=True)

if not os.path.exists(EQUITY_FILE):
    with open(EQUITY_FILE, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "symbol", "direction", "entry", "exit", "pnl", "equity"])

# Начальный баланс можно вынести в .env / settings.py
INITIAL_BALANCE = 1000
current_equity = INITIAL_BALANCE

def log_equity(symbol: str, direction: str, entry: float, exit_price: float, size: float, status: str) -> None:
    global current_equity

    if status != "executed":
        return  # только реальные сделки

    # расчёт PnL (проще: (выход - вход) * размер * направленность)
    pnl = (exit_price - entry) * size if direction == "long" else (entry - exit_price) * size
    current_equity += pnl

    with open(EQUITY_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.utcnow().isoformat(), symbol, direction, entry, exit_price, round(pnl, 4), round(current_equity, 4),
        ])

    print(f"📈 Equity updated: {current_equity:.2f} | PnL: {pnl:.2f}")
