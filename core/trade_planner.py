from position_manager.advanced_risk_manager import AdvancedRiskManager
from utils.dynamic_sl_tp import get_dynamic_sl_tp, get_trailing_config


class TradePlanner:
    def __init__(self, balance: float, confidence: float, entry_price: float, direction: str):
        self.balance = balance
        self.confidence = confidence
        self.entry_price = entry_price
        self.direction = direction.lower()
        self.risk_manager = AdvancedRiskManager()

    def generate(self) -> dict:
        # 1. Получаем SL/TP и структуру выхода
        sltp = get_dynamic_sl_tp(self.confidence, self.entry_price, self.direction)

        # 2. Расчёт размера позиции
        normalized_conf = self.confidence / 100  # Преобразование к [0..1]
        size = self.risk_manager.calculate_position_size(
            balance=self.balance,
            entry=self.entry_price,
            stop=sltp["sl"],
            confidence_score=normalized_conf,
        )

        # 3. Трейлинг-параметры
        trailing = get_trailing_config(self.confidence)

        # 4. Возвращаем объединённый план сделки
        return {
            "size": size,
            **sltp,
            "trailing": trailing,
        }
