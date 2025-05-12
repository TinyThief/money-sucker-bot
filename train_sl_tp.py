from tools.sl_tp_optimizer import run_optimizer
from datetime import datetime

def main():
    print(f"📈 Запуск обучения SL/TP — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    run_optimizer()
    print("✅ Обучение завершено. Весы сохранены.")

if __name__ == "__main__":
    main()
#     print("✅ Обучение завершено. Весы сохранены.")
#     run_optimizer()