from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    symbol = Column(String)
    direction = Column(String)
    price = Column(Float)
    sl = Column(Float)
    tp = Column(Float)
    size = Column(Float)
    confidence = Column(Float)
    reasons = Column(String)  # json.dumps(list[str]) or semicolon string
    status = Column(String)
    result = Column(String)
    pnl = Column(Float)


engine = create_engine("sqlite:///data/bot.db")
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
