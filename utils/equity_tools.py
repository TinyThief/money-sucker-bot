from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def generate_equity_curve(
    log_file: str = "logs/signal_log.csv",
    output_file: str = "logs/equity_curve.png",
) -> bool | None:
    log_path = Path(log_file)
    output_path = Path(output_file)

    if not log_path.exists():
        print(f"Файл {log_file} не найден.")
        return False

    try:
        columns = [
            "timestamp", "symbol", "direction", "entry_price", "sl_price", "tp_price",
            "size", "confidence", "reasons", "status", "result",
        ]
        df = pd.read_csv(log_path, header=None, names=columns)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")

        df["virtual_size"] = 100 / df["entry_price"]
        df["pnl"] = df.apply(
            lambda row:
                (row["tp_price"] - row["entry_price"]) * row["virtual_size"] if row["result"] == "tp"
                else (row["sl_price"] - row["entry_price"]) * row["virtual_size"] if row["result"] == "sl"
                else 0,
            axis=1,
        )
        df["equity"] = df["pnl"].cumsum()

        # Построение графика
        plt.figure(figsize=(10, 5))
        plt.plot(df["timestamp"], df["equity"], label="Equity Curve (100 USDT Size)")
        plt.title("Кривая капитала по сигналам")
        plt.xlabel("Дата")
        plt.ylabel("Баланс (USDT)")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()

        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path)
        plt.close()

    except OSError as e:
        print(f"Ошибка при построении графика equity: {e}")
        return False

    else:
        print(f"✅ График сохранён в {output_file}")
        return True
