import os
import json
import pandas as pd

SIGNAL_LOG_PATH = "logs/signal_log.csv"
WEIGHTS_DIR = "config/profiles/"

THRESHOLD = 50


def load_profiles():
    profiles = {}
    for file in os.listdir(WEIGHTS_DIR):
        if file.endswith(".json"):
            with open(os.path.join(WEIGHTS_DIR, file), encoding="utf-8") as f:
                data = json.load(f)
                profiles[file] = data.get("weights", {})
    return profiles


def evaluate_profile(df, weights):
    total, tp = 0, 0
    for _, row in df.iterrows():
        reasons = str(row["reasons"]).split("; ")
        conf = sum(weights.get(r.strip(), 0) for r in reasons)
        if conf >= THRESHOLD:
            total += 1
            if row["result"] == "tp":
                tp += 1
    win_rate = tp / total if total else 0
    return win_rate, total


def run_ab_test():
    if not os.path.exists(SIGNAL_LOG_PATH):
        print("Нет сигналов для анализа")
        return

    df = pd.read_csv(SIGNAL_LOG_PATH, header=None)
    df.columns = [
        "timestamp", "symbol", "direction", "entry_price", "sl_price", "tp_price",
        "size", "confidence", "reasons", "status", "result", "pnl"
    ]
    df = df.dropna(subset=["reasons", "result"])

    profiles = load_profiles()
    print("\n📊 A/B Тест профилей confident-весов:")
    for name, weights in profiles.items():
        win_rate, total = evaluate_profile(df, weights)
        print(f"• {name}: {win_rate:.2%} (на {total} сделках)")


if __name__ == "__main__":
    run_ab_test()