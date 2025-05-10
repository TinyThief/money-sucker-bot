from log_setup import logger
from utils.telegram_utils import send_telegram_message
from typing import Dict, Union

last_known_status: Dict[str, Union[bool, None]] = {
    "strategies_running": None,
    "connection_ok": None,
}

async def send_event_heartbeat(event_text: str) -> None:
    try:
        message = f"🛡 <b>HEARTBEAT-Событие:</b>\n\n{event_text}\n\n✅ Бот работает."
        await send_telegram_message(message)
        logger.info(f"📨 Heartbeat отправлен: {event_text}")
    except Exception as e:
        logger.error(f"Ошибка отправки Event-Heartbeat: {e}")
    