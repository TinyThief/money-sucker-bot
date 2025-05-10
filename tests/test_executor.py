import unittest
from unittest.mock import patch, MagicMock
from trade_executor_core import place_order


class TestTradeExecutor(unittest.TestCase):
    @patch("trade_executor_core.exchange")
    def test_place_order_success(self, mock_exchange) -> None:
        mock_exchange.create_order.return_value = {"id": "order123", "status": "open"}

        result = place_order("ETH/USDT", "buy", 0.1, 1800, 1900)

        self.assertTrue(result)
        mock_exchange.create_order.assert_any_call(
            symbol="ETH/USDT",
            type="market",
            side="Buy",
            amount=0.1,
            params={"category": "linear"}
        )

if __name__ == "__main__":
    unittest.main()
