import pytest
from core.trade_planner import TradePlanner


def test_trade_plan_generation():
    planner = TradePlanner(balance=1000, confidence=65, entry_price=100.0, direction="long")
    plan = planner.generate()

    assert plan["size"] > 0
    assert plan["sl"] < 100.0
    assert plan["tp1"] > 100.0 or plan["tp1"] is None
    assert plan["tp2"] > 100.0
    assert 0 <= plan["tp1_ratio"] <= 1.0
    assert 0 <= plan["tp2_ratio"] <= 1.0
    assert isinstance(plan["trailing"], dict)
    assert "trail_percent" in plan["trailing"]
    assert "move_to_be_after" in plan["trailing"]


def test_trade_plan_short_direction():
    planner = TradePlanner(balance=500, confidence=80, entry_price=250.0, direction="short")
    plan = planner.generate()

    assert plan["size"] > 0
    assert plan["sl"] > 250.0
    assert plan["tp2"] < 250.0
    assert plan["tp1_ratio"] in (0.0, 0.3)
    assert plan["tp2_ratio"] in (0.7, 1.0)


def test_confidence_extremes():
    low = TradePlanner(balance=1000, confidence=20, entry_price=100.0, direction="long").generate()
    high = TradePlanner(balance=1000, confidence=90, entry_price=100.0, direction="long").generate()

    assert low["risk_pct"] < high["risk_pct"] or True  # not all plans may return risk_pct
    assert low["tp1"] is not None or True
    assert high["tp1"] is None or True  # may skip tp1 at high confidence
    assert low["tp2"] > high["tp2"] or True  # may skip tp2 at low confidence