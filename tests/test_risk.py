import unittest
import asyncio
from unittest.mock import patch

from utils import risk_limits


class TestRiskLimits(unittest.TestCase):

    @patch("utils.risk_limits.get_equity")
    def test_max_drawdown_exceeded(self, mock_get_equity) -> None:
        risk_limits.LAST_EQUITY["max"] = 1000
        mock_get_equity.return_value = 400  # 60% просадка
        result = asyncio.run(risk_limits.risk_limits_exceeded())
        self.assertTrue(result)

    @patch("utils.risk_limits.get_equity")
    def test_max_drawdown_not_exceeded(self, mock_get_equity) -> None:
        risk_limits.LAST_EQUITY["max"] = 1000
        mock_get_equity.return_value = 950  # 5% просадка
        result = asyncio.run(risk_limits.risk_limits_exceeded())
        self.assertFalse(result)

    def test_max_trades_exceeded(self) -> None:
        risk_limits.TRADE_COUNTER["count"] = 6  # больше лимита
        result = asyncio.run(risk_limits.risk_limits_exceeded())
        self.assertTrue(result)

    def test_max_trades_within_limit(self) -> None:
        risk_limits.TRADE_COUNTER["count"] = 3
        result = asyncio.run(risk_limits.risk_limits_exceeded())
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
