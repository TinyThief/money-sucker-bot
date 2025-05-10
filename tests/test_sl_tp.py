import unittest

from position_manager.manager import calculate_sl_tp


class TestSLTP(unittest.TestCase):
    def test_long_position(self) -> None:
        result = calculate_sl_tp(entry=100.0, direction="long", rr=2.0, sl_pct=0.01)
        assert result is not None
        self.assertAlmostEqual(result["stop_loss"], 99.0, places=4)
        self.assertAlmostEqual(result["take_profit"], 102.0, places=4)

    def test_short_position(self) -> None:
        result = calculate_sl_tp(entry=100.0, direction="short", rr=2.0, sl_pct=0.01)
        assert result is not None
        self.assertAlmostEqual(result["stop_loss"], 101.0, places=4)
        self.assertAlmostEqual(result["take_profit"], 98.0, places=4)

    def test_invalid_entry(self) -> None:
        result = calculate_sl_tp(entry=0, direction="long", rr=2.0, sl_pct=0.01)
        assert result is None

    def test_invalid_direction(self) -> None:
        result = calculate_sl_tp(entry=100.0, direction="sideways", rr=2.0, sl_pct=0.01)
        assert result is None

    def test_invalid_rr_or_sl(self) -> None:
        result = calculate_sl_tp(entry=100.0, direction="long", rr=0, sl_pct=0)
        assert result is None

if __name__ == "__main__":
    unittest.main()
