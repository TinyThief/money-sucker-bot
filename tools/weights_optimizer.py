import json
from collections import defaultdict
import pandas as pd

# 🔧 Настройки
LOG_FILE = "logs/signal_log.csv"
WEIGHTS_FILE = "config/best_weights.json"
OUTPUT_FILE = "config/best_weights_optimized.json"

# ⚙️ Загрузим логи сигналов
def load_logs():
    try:
        return pd.read_csv(LOG_FILE)
    except Exception as e:
        print(f"Ошибка загрузки логов сигналов: {e}")
        return pd.DataFrame()

# 📊 Анализ успешности каждого признака
def analyze_weights(df):
    stats = defaultdict(lambda: {"tp": 0, "sl": 0, "count": 0})

    for _, row in df.iterrows():
        if pd.isna(row.get("reasons")) or pd.isna(row.get("result")):
            continue

        try:
            reasons = json.loads(row["reasons"]) if isinstance(row["reasons"], str) else row["reasons"]
            result = row["result"].lower().strip()
            for reason in reasons:
                key = reason.replace("✅", "").replace("📍", "").replace(":", "").strip()
                stats[key]["count"] += 1
                if result == "tp":
                    stats[key]["tp"] += 1
                elif result == "sl":
                    stats[key]["sl"] += 1
        except Exception as e:
            print(f"Ошибка разбора строки: {e}")
            continue

    return stats

# 📈 Генерация новых весов по результатам
def generate_weights(stats, base_weight=10, scale=40):
    new_weights = {}
    for key, values in stats.items():
        total = values["count"]
        if total == 0:
            continue
        success_ratio = values["tp"] / total
        weight = base_weight + round((success_ratio - 0.5) * scale)
        weight = max(0, weight)  # не может быть < 0
        new_weights[key] = weight
    return new_weights

# 💾 Сохраняем новый файл весов
def save_weights(weights) -> None:
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(weights, f, ensure_ascii=False, indent=2)
        print(f"✅ Обновлённые веса сохранены в {OUTPUT_FILE}")
    except Exception as e:
        print(f"Ошибка сохранения: {e}")

# 🚀 Основной процесс
def optimize() -> None:
    df = load_logs()
    if df.empty:
        print("Нет данных для анализа.")
        return
    stats = analyze_weights(df)
    new_weights = generate_weights(stats)
    save_weights(new_weights)

# 🧠 Функция для использования из других модулей
def optimize_weights_from_logs(log_path="logs/signal_log.csv"):
    df = pd.read_csv(log_path)
    stats = analyze_weights(df)
    return generate_weights(stats)

if __name__ == "__main__":
    optimize()
