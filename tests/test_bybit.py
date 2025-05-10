import pytest
from unittest.mock import AsyncMock, patch
from api import bybit_async


@pytest.mark.asyncio
@patch("api.bybit_async.get_exchange")
async def test_get_open_position(mock_get_exchange):
    mock_exchange = AsyncMock()

    mock_exchange.fetch_positions.return_value = [{
        "symbol": "BTC/USDT",
        "contracts": 0.05,
        "side": "long",
        "entryPrice": 28000,
        "unrealisedPnl": 30,
    }]

    mock_get_exchange.return_value = mock_exchange

    result = await bybit_async.get_open_position("BTC/USDT")

    assert result is not None
    assert result["size"] == 0.05
    assert result["side"] == "long"
    assert result["entry"] == 28000
