import unittest
from utils.direction import determine_direction


class TestDirectionLogic(unittest.TestCase):
    def test_trend_up_with_liquidity_above(self) -> None:
        result = determine_direction("bullish", "above_eqh")
        assert result == "long"

    def test_trend_down_with_liquidity_below(self) -> None:
        result = determine_direction("bearish", "below_eql")
        assert result == "short"

    def test_trend_up_with_liquidity_below(self) -> None:
        result = determine_direction("bullish", "below_eql")
        assert result == "neutral"

    def test_trend_down_with_liquidity_above(self) -> None:
        result = determine_direction("bearish", "above_eqh")
        assert result == "neutral"

    def test_invalid_inputs(self) -> None:
        result = determine_direction(None, None)
        assert result == "neutral"


if __name__ == "__main__":
    unittest.main()
