import asyncio

from position_manager.monitor import monitor_all_positions_loop


def run_async_tasks() -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(monitor_all_positions_loop())
