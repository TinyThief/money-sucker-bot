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


# 📉 Новая функция: построение графика просадки
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
            print("❌ Недопустимый формат журнала.")
            return None

        df["time"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce").fillna(0)
        df = df.dropna(subset=["time"])
        df = df.sort_values("time")

        df["equity"] = starting_equity + df["pnl"].cumsum()
        df["high_watermark"] = df["equity"].cummax()
        df["drawdown"] = df["equity"] - df["high_watermark"]

        plt.figure(figsize=(10, 5))
        plt.plot(df["time"], df["drawdown"], label="Drawdown", color="red")
        plt.title("📉 Drawdown Curve")
        plt.xlabel("Дата")
        plt.ylabel("Просадка USDT")
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


# 💼 Новая функция: текущий equity
def get_equity_balance(
    log_file: str = "logs/trade_journal.csv",
    starting_equity: float = 1000
) -> float:
    if not os.path.exists(log_file):
        return starting_equity
    try:
        df = pd.read_csv(log_file)
        df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce").fillna(0)
        total_pnl = df["pnl"].sum()
        return starting_equity + total_pnl
    except Exception as e:
        print(f"❌ Ошибка чтения equity: {e}")
        return starting_equity
