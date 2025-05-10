import json
import os
from collections import defaultdict

import pandas as pd


def optimize_confidence_weights(signal_log_csv="logs/signal_log.csv", output_json="config/confidence_weights.json") -> bool:
    if not os.path.exists(signal_log_csv):
        print("❌ Лог сигналов не найден.")
        return False

    df = pd.read_csv(signal_log_csv, header=None)
    df.columns = [
        "timestamp", "symbol", "direction", "entry_price", "sl_price", "tp_price",
        "size", "confidence", "reasons", "status", "result", "pnl",
    ]

    counts = defaultdict(lambda: {"tp": 0, "sl": 0})

    for _, row in df.iterrows():
        if row["result"] not in ["tp", "sl"]:
            continue
        reason_list = str(row["reasons"]).split("; ")
        for reason in reason_list:
            if row["result"] == "tp":
                counts[reason]["tp"] += 1
            else:
                counts[reason]["sl"] += 1

    weights = {}
    for reason, stats in counts.items():
        total = stats["tp"] + stats["sl"]
        score = 50 if total == 0 else int(stats["tp"] / total * 100)
        weights[reason] = score

    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(weights, f, indent=4)

    print(f"✅ Обновлены confident веса и сохранены в {output_json}")
    return True
