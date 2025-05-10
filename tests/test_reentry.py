import time
import unittest

from strategies import smc_strategy


class TestReentryLogic(unittest.TestCase):
    def setUp(self) -> None:
        smc_strategy.ENTRY_CACHE.clear()

    def test_first_entry_allowed(self) -> None:
        assert smc_strategy.allow_reentry("BTCUSDT", 10000, "long")

    def test_block_same_price_direction_within_timeout(self) -> None:
        smc_strategy.update_entry_cache("BTCUSDT", 10000, "long")
        assert not smc_strategy.allow_reentry("BTCUSDT", 10000, "long")

    def test_allow_if_price_deviates(self) -> None:
        smc_strategy.update_entry_cache("BTCUSDT", 10000, "long")
        assert smc_strategy.allow_reentry("BTCUSDT", 10100, "long")  # >0.5%

    def test_allow_if_direction_changes(self) -> None:
        smc_strategy.update_entry_cache("BTCUSDT", 10000, "long")
        assert smc_strategy.allow_reentry("BTCUSDT", 10000, "short")

    def test_allow_if_timeout_passed(self) -> None:
        smc_strategy.ENTRY_CACHE["BTCUSDT"] = {
            "price": 10000,
            "ts": time.time() - 3600,  # > ENTRY_TIMEOUT
            "direction": "long",
        }
        assert smc_strategy.allow_reentry("BTCUSDT", 10000, "long")

if __name__ == "__main__":
    unittest.main()
