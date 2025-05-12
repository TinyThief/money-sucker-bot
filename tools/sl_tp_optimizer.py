import pandas as pd
import json
import os
from collections import defaultdict

LOG_FILE = "logs/signal_log.csv"
OUTPUT_FILE = "config/sl_tp_weights.json"


def load_logs():
    if not os.path.exists(LOG_FILE):
        print(f"❌ Лог-файл не найден: {LOG_FILE}")
        return pd.DataFrame()
    df = pd.read_csv(LOG_FILE)
    df = df.dropna(subset=["sl", "tp", "price", "confidence", "result"])
    return df


def bucket_confidence(conf: float) -> str:
    if conf < 40:
        return "low_confidence"
    elif conf < 70:
        return "mid_confidence"
    else:
        return "high_confidence"


def analyze_optimal_sl_tp(df: pd.DataFrame):
    stats = defaultdict(lambda: defaultdict(list))

    for _, row in df.iterrows():
        symbol = row["symbol"]
        group = bucket_confidence(row["confidence"])
        sl_dist = abs(row["price"] - row["sl"])
        rr_ratio = abs(row["tp"] - row["price"]) / sl_dist if sl_dist > 0 else 1.5
        result = row["result"]

        stats[symbol][group].append({
            "sl": sl_dist,
            "rr": rr_ratio,
            "success": 1 if result == "tp" else 0
        })

    weights = {}
    for symbol, conf_groups in stats.items():
        weights[symbol] = {}
        for group, records in conf_groups.items():
            if not records:
                continue
            df_group = pd.DataFrame(records)
            grouped = df_group.groupby(["sl", "rr"]).agg(["mean", "count"])
            grouped.columns = ["_".join(col) for col in grouped.columns]
            grouped = grouped.reset_index()
            grouped["score"] = grouped["success_mean"] * grouped["success_count"]
            best = grouped.sort_values("score", ascending=False).iloc[0]
            weights[symbol][group] = {
                "sl_buffer": round(best["sl"], 4),
                "tp_rr": round(best["rr"], 2)
            }

    return weights


def save_weights(weights):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(weights, f, indent=2, ensure_ascii=False)
    print(f"✅ Конфигурация SL/TP сохранена в {OUTPUT_FILE}")


def run_optimizer():
    df = load_logs()
    if df.empty:
        print("⚠️ Нет данных для анализа.")
        return
    weights = analyze_optimal_sl_tp(df)
    save_weights(weights)


if __name__ == "__main__":
    run_optimizer()