from sqlalchemy.orm import Session
from database.schema import SessionLocal, Signal
from datetime import datetime
from typing import Optional

def save_signal(
    symbol: str,
    direction: str,
    price: float,
    sl: float,
    tp: float,
    size: float,
    confidence: float,
    reasons: str,
    status: str = "pending",
    result: str = "",
    pnl: float = 0.0,
    timestamp: Optional[datetime] = None
):
    session: Session = SessionLocal()
    try:
        signal = Signal(
            timestamp=timestamp or datetime.utcnow(),
            symbol=symbol,
            direction=direction,
            price=price,
            sl=sl,
            tp=tp,
            size=size,
            confidence=confidence,
            reasons=reasons,
            status=status,
            result=result,
            pnl=pnl
        )
        session.add(signal)
        session.commit()
        print(f"✅ Сигнал сохранён в базу: {symbol} {direction} @ {price}")
    except Exception as e:
        session.rollback()
        print(f"❌ Ошибка при сохранении сигнала: {e}")
    finally:
        session.close()
def get_signals():
    session: Session = SessionLocal()
    try:
        signals = session.query(Signal).all()
        return signals
    except Exception as e:
        print(f"❌ Ошибка при получении сигналов: {e}")
        return []
    finally:
        session.close()