from unittest.mock import patch, MagicMock
import trade_executor_core as executor


@patch("trade_executor_core.place_stop_loss_order")
@patch("trade_executor_core.place_take_profit_order")
@patch("trade_executor_core.place_market_order")
def test_place_order_with_tp1_tp2(mock_market, mock_tp, mock_sl) -> None:
    mock_market.return_value = {"id": "mock_order"}
    mock_tp.return_value = {"id": "tp_order"}
    mock_sl.return_value = {"id": "sl_order"}

    result = executor.place_order(
        symbol="BTC/USDT",
        side="buy",
        size=0.1,
        sl=27000,
        tp1=28500,
        tp2=29000,
        tp1_ratio=0.4,
    )

    assert result is True
    mock_market.assert_called_once_with("BTC/USDT", "buy", 0.1)
    assert mock_tp.call_count == 2
    mock_sl.assert_called_once_with("BTC/USDT", "buy", 27000, 0.1)


@patch("trade_executor_core.place_stop_loss_order")
@patch("trade_executor_core.place_take_profit_order")
@patch("trade_executor_core.place_market_order")
def test_place_order_only_tp2(mock_market, mock_tp, mock_sl) -> None:
    mock_market.return_value = {"id": "mock_order"}
    mock_tp.return_value = {"id": "tp2_order"}
    mock_sl.return_value = {"id": "sl_order"}

    result = executor.place_order(
        symbol="BTC/USDT",
        side="sell",
        size=0.15,
        sl=31000,
        tp1=None,
        tp2=29000,
    )

    assert result is True
    mock_market.assert_called_once_with("BTC/USDT", "sell", 0.15)
    mock_tp.assert_called_once_with("BTC/USDT", "sell", 29000, 0.15)
    mock_sl.assert_called_once_with("BTC/USDT", "sell", 31000, 0.15)


@patch("trade_executor_core.get_exchange")
@patch("trade_executor_core.get_open_position")
def test_market_close_partial(mock_get_position, mock_get_exchange) -> None:
    mock_get_position.return_value = {
        "side": "buy",
        "size": 0.2,
        "entry": 100,
    }

    mock_exchange = MagicMock()
    mock_exchange.fetch_ticker.return_value = {"last": 110}
    mock_exchange.create_order.return_value = {"id": "partial_close_order"}
    mock_get_exchange.return_value = mock_exchange

    executor.TRADING_DISABLED = False
    result = executor.market_close_partial("BTC/USDT", 0.1)

    assert result is True
    mock_exchange.create_order.assert_called_once_with(
        symbol="BTC/USDT",
        type="market",
        side="Sell",
        amount=0.1,
        params={"reduceOnly": True, "category": "linear"},
    )
