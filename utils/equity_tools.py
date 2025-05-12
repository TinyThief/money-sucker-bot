import os
import pandas as pd
import matplotlib.pyplot as plt


def plot_equity_curve(
    log_file: str = "logs/trade_journal.csv",
    save_path: str = "logs/equity_curve.png",
    starting_equity: float = 1000
):
    if not os.path.exists(log_file):
        print(f"❌ Файл журнала не найден: {log_file}")
        return None

    try:
        df = pd.read_csv(log_file)
        if "timestamp" not in df.columns or "pnl" not in df.columns:
            print("❌ Недопустимый формат журнала: нет столбцов 'timestamp' и 'pnl'")
            return None

        df["time"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce").fillna(0)
        df = df.dropna(subset=["time"])
        df = df.sort_values("time")

        if df.empty or df["pnl"].abs().sum() == 0:
            print("⚠️ Недостаточно данных для построения equity.")
            return None

        df["equity"] = starting_equity + df["pnl"].cumsum()

        plt.figure(figsize=(10, 5))
        plt.plot(df["time"], df["equity"], label="Equity", color="blue")
        plt.title("📊 Equity Curve")
        plt.xlabel("Дата")
        plt.ylabel("Баланс USDT")
        plt.grid(True)
        plt.tight_layout()
        plt.legend()

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path)
        plt.close()

        return save_path

    except Exception as e:
        print(f"❌ Ошибка построения equity: {e}")
        return None


def plot_drawdown_curve(
    log_file: str = "logs/trade_journal.csv",
    save_path: str = "logs/drawdown_curve.png",
    starting_equity: float = 1000
):
    if not os.path.exists(log_file):
        print(f"❌ Файл журнала не найден: {log_file}")
        return None

    try:
        df = pd.read_csv(log_file)
        if "timestamp" not in df.columns or "pnl" not in df.columns:
            print("❌ Неверный формат: нет 'timestamp' и 'pnl'")
            return None

        df["time"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce").fillna(0)
        df = df.dropna(subset=["time"])
        df = df.sort_values("time")

        if df.empty or df["pnl"].abs().sum() == 0:
            print("⚠️ Недостаточно данных для построения drawdown.")
            return None

        df["equity"] = starting_equity + df["pnl"].cumsum()
        df["rolling_max"] = df["equity"].cummax()
        df["drawdown"] = df["equity"] - df["rolling_max"]
        df["drawdown_pct"] = df["drawdown"] / df["rolling_max"] * 100

        plt.figure(figsize=(10, 5))
        plt.plot(df["time"], df["drawdown_pct"], color="red", label="Drawdown %")
        plt.title("📉 Drawdown Curve")
        plt.xlabel("Дата")
        plt.ylabel("Просадка (%)")
        plt.grid(True)
        plt.tight_layout()
        plt.legend()

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path)
        plt.close()

        return save_path

    except Exception as e:
        print(f"❌ Ошибка построения drawdown: {e}")
        return None


def get_equity_balance(log_file: str = "logs/trade_journal.csv", starting_equity: float = 1000) -> float:
    if not os.path.exists(log_file):
        print("❌ Файл equity не найден")
        return starting_equity

    try:
        df = pd.read_csv(log_file)
        if "pnl" not in df.columns:
            print("❌ Нет колонки 'pnl' в журнале")
            return starting_equity

        df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce").fillna(0)
        total_pnl = df["pnl"].sum()
        return round(starting_equity + total_pnl, 2)

    except Exception as e:
        print(f"❌ Ошибка расчета equity баланса: {e}")
        return starting_equity
