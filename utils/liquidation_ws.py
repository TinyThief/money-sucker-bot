import asyncio
import json
from collections import deque

import websockets

# Глобальный буфер последних ликвидаций (ограничим 100 событиями)
recent_liquidations = deque(maxlen=100)

async def liquidation_listener(symbol: str = "BTCUSDT") -> None:
    url = "wss://stream.bybit.com/v5/public/linear"
    topic = f"liquidation.{symbol}"

    async with websockets.connect(url) as ws:
        # Подписка на канал ликвидаций
        subscribe_msg = {
            "op": "subscribe",
            "args": [topic],
        }
        await ws.send(json.dumps(subscribe_msg))

        while True:
            try:
                message = await ws.recv()
                data = json.loads(message)

                if data.get("topic") == topic and "data" in data:
                    for event in data["data"] if isinstance(data["data"], list) else [data["data"]]:
                        price = float(event["price"])
                        side = event["side"]
                        qty = float(event["qty"])

                        if qty >= 50000:  # фильтрация по объёму ликвидации
                            recent_liquidations.append({
                                "price": price,
                                "side": side,
                                "qty": qty,
                            })
            except Exception as e:
                print(f"WebSocket error: {e}")
                await asyncio.sleep(5)

# Пример запуска (для ручного теста):
# asyncio.run(liquidation_listener("BTCUSDT"))
