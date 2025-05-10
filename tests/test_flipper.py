import unittest
from unittest.mock import patch, AsyncMock
from position_manager.position_flipper import flip_position


class TestFlipPosition(unittest.TestCase):

    @patch("position_manager.position_flipper.safe_execute", new_callable=AsyncMock)
    @patch("position_manager.position_flipper.get_open_position")
    def test_flip_no_existing_position(self, mock_get_open, mock_safe_execute) -> None:
        mock_get_open.return_value = None
        mock_safe_execute.return_value = {"symbol": "BTC/USDT", "side": "buy", "size": 1.0, "entry_price": 100.0}

        result = flip_position("BTC/USDT", "buy", 1.0, 100.0, 120.0)
        assert result
        assert mock_safe_execute.call_count == 1  # only place_order

    @patch("position_manager.position_flipper.safe_execute", new_callable=AsyncMock)
    @patch("position_manager.position_flipper.get_open_position")
    def test_flip_same_direction(self, mock_get_open, mock_safe_execute) -> None:
        mock_get_open.return_value = {
            "symbol": "BTC/USDT", "side": "long", "size": 1.0, "entry_price": 100.0,
        }

        result = flip_position("BTC/USDT", "buy", 1.0, 100.0, 120.0)
        assert not result
        mock_safe_execute.assert_not_called()

    @patch("position_manager.position_flipper.safe_execute", new_callable=AsyncMock)
    @patch("position_manager.position_flipper.get_open_position")
    def test_flip_opposite_direction_success(self, mock_get_open, mock_safe_execute) -> None:
        mock_get_open.return_value = {
            "symbol": "BTC/USDT", "side": "short", "size": 1.0, "entry_price": 100.0,
        }
        mock_safe_execute.side_effect = [
            True,  # close_position
            {"symbol": "BTC/USDT", "side": "buy", "size": 1.0, "entry_price": 100.0}  # place_order
        ]

        result = flip_position("BTC/USDT", "buy", 1.0, 100.0, 120.0)
        assert result
        assert mock_safe_execute.call_count == 2

    @patch("position_manager.position_flipper.safe_execute", new_callable=AsyncMock)
    @patch("position_manager.position_flipper.get_open_position")
    def test_flip_opposite_direction_close_fail(self, mock_get_open, mock_safe_execute) -> None:
        mock_get_open.return_value = {
            "symbol": "BTC/USDT", "side": "short", "size": 1.0, "entry_price": 100.0,
        }
        mock_safe_execute.return_value = None  # close fails

        result = flip_position("BTC/USDT", "buy", 1.0, 100.0, 120.0)
        assert not result
        assert mock_safe_execute.call_count == 1  # only close attempted


if __name__ == "__main__":
    unittest.main()
