import asyncio
from utils.telegram_utils import send_telegram_message

def send_telegram_alert(message: str) -> None:
    asyncio.run(send_telegram_message(message))
