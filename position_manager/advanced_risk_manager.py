from log_setup import logger
from typing import Optional

class AdvancedRiskManager:
    def __init__(self, max_risk_pct=0.01, min_risk_pct=0.002, daily_loss_limit=0.03, max_drawdown_pct=0.05):
        self.max_risk_pct = max_risk_pct
        self.min_risk_pct = min_risk_pct
        self.daily_loss_limit = daily_loss_limit
        self.max_drawdown_pct = max_drawdown_pct

        self.start_balance: Optional[float] = None
        self.current_balance: Optional[float] = None
        self.equity_high: Optional[float] = None

    def set_equity(self, balance: float) -> None:
        if balance is None:
            return
        if self.start_balance is None:
            self.start_balance = balance
            self.equity_high = balance
        self.current_balance = balance
        self.equity_high = max(self.equity_high or 0.0, balance)

    def allowed_to_trade(self) -> bool:
        if self.start_balance is None or self.current_balance is None or self.equity_high is None:
            return False
        loss = self.start_balance - self.current_balance
        if loss >= self.start_balance * self.daily_loss_limit:
            logger.warning("⛔ Превышен дневной лимит убытков.")
            return False
        drawdown = (self.equity_high - self.current_balance) / self.equity_high
        if drawdown >= self.max_drawdown_pct:
            logger.warning("📉 Превышен лимит просадки.")
            return False
        return True

    def risk_pct_from_confidence(self, score: float) -> float:
        score = max(min(score, 1.0), 0.0)
        return self.min_risk_pct + (self.max_risk_pct - self.min_risk_pct) * score

    def calculate_position_size(self, balance: float, entry: float, stop: float, confidence_score: float) -> float:
        if balance is None or entry is None or stop is None or entry <= 0 or stop <= 0:
            logger.error("❌ Некорректные значения balance, entry или stop.")
            return 0.0
        sl_distance = abs(entry - stop)
        if sl_distance == 0:
            logger.error("❌ SL расстояние равно 0.")
            return 0.0
        risk_pct = self.risk_pct_from_confidence(confidence_score)
        risk_amount = balance * risk_pct
        size = risk_amount / sl_distance
        return round(size, 4)
