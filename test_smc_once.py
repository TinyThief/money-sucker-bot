import asyncio
from strategies.smc_strategy import run_smc_strategy

async def test():
    await run_smc_strategy("BTCUSDT", capital=1000)

if __name__ == "__main__":
    asyncio.run(test())
#     await asyncio.sleep(30)
#     continue