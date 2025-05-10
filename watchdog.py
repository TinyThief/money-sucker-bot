import logging
import subprocess
import time
import asyncio
import psutil

from utils.telegram_utils import send_telegram_message

# === НАСТРОЙКИ ===
TARGET_SCRIPT = "launcher_async.py"
CHECK_INTERVAL = 30
AUTO_RESTART = True
USE_TELEGRAM = True

# Логи
logging.basicConfig(
    filename="logs/watchdog.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

def send_async_message(message: str):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(send_telegram_message(message))
        else:
            asyncio.run(send_telegram_message(message))
    except RuntimeError:
        asyncio.run(send_telegram_message(message))

def is_script_running(script_name) -> bool:
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmdline = proc.info.get("cmdline")
            if cmdline and script_name in cmdline:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False

def launch_script(script_name) -> None:
    logging.info(f"🚀 Перезапуск {script_name}...")
    subprocess.Popen(["python", script_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if USE_TELEGRAM:
        send_async_message(f"🛠 Бот <code>{script_name}</code> был перезапущен watchdog'ом.")
    print(f"[watchdog] {script_name} перезапущен.")

if __name__ == "__main__":
    print("👁 Watchdog следит за ботом...")

    while True:
        try:
            if not is_script_running(TARGET_SCRIPT):
                logging.warning(f"💀 {TARGET_SCRIPT} не найден в процессах.")
                if USE_TELEGRAM:
                    send_async_message(f"⚠️ Бот <code>{TARGET_SCRIPT}</code> упал или не запущен.")
                if AUTO_RESTART:
                    launch_script(TARGET_SCRIPT)
            else:
                logging.info(f"✅ {TARGET_SCRIPT} работает нормально.")
        except Exception as e:
            logging.exception(f"[Watchdog Error] {e}")
        time.sleep(CHECK_INTERVAL)