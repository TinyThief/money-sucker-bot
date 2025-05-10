import os
import pandas as pd
from datetime import timedelta
from tools.weights_optimizer import optimize_weights_from_logs
from backtest.smc_backtest import run_backtest_on_df  # предполагаем, что есть


def walk_forward_run(
    symbol: str,
    filepath: str,
    window_size_days: int = 90,
    test_size_days: int = 30,
    confidence_base: float = 65.0
):
    df = pd.read_csv(filepath)
    if "timestamp" not in df.columns:
        df.insert(0, "timestamp", pd.date_range(start="2022-01-01", periods=len(df), freq="h"))
    df = df.sort_values("timestamp")
    start_idx = 0
    end_idx = len(df) - 1

    all_results = []

    while True:
        train_end = df["timestamp"].iloc[start_idx] + timedelta(days=window_size_days)
        test_end = train_end + timedelta(days=test_size_days)

        train_df = df[(df["timestamp"] >= df["timestamp"].iloc[start_idx]) & (df["timestamp"] < train_end)]
        test_df = df[(df["timestamp"] >= train_end) & (df["timestamp"] < test_end)]

        if len(test_df) < 50:
            break

        print(f"🧠 Train: {train_df['timestamp'].min()} → {train_df['timestamp'].max()}")
        print(f"🧪 Test : {test_df['timestamp'].min()} → {test_df['timestamp'].max()}")

        # 1. Генерируем сигналы на train и логируем
        run_backtest_on_df(symbol, train_df, confidence_base, log_signals=True)

        # 2. Оптимизируем веса по log_signal.csv
        weights = optimize_weights_from_logs("logs/signal_log.csv")

        # 3. Применяем эти веса на test
        test_result = run_backtest_on_df(symbol, test_df, confidence_base, log_signals=False, use_weights=weights)
        if not test_result.empty:
            all_results.append(test_result)
            print(f"✅ Test window trades: {len(test_result)}")
        else:
            print("⚠️ Нет сделок в этом окне теста.")

        # Сдвигаем окно
        start_idx = df[df["timestamp"] >= test_end].index.min()
        if pd.isna(start_idx):
            break

    return pd.concat(all_results, ignore_index=True)


if __name__ == "__main__":
    results = walk_forward_run(
        symbol="BTCUSDT",
        filepath="data/historical/BTCUSDT_1h.csv",
        window_size_days=90,
        test_size_days=30,
        confidence_base=65.0
    )

    os.makedirs("logs", exist_ok=True)
    results.to_csv("logs/walkforward_results.csv", index=False)
    print("\n✅ Walk-forward завершён. Итоги:")
    print(results.tail())
