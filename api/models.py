from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, Enum
from sqlalchemy.orm import relationship
from .database import Base
import enum

class TradeType(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"

class TradeStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PENDING = "PENDING"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    balance = Column(Float, default=10000.0)
    is_active = Column(Boolean, default=True)
    
    trades = relationship("Trade", back_populates="owner")
    trade_history = relationship("TradeHistory", back_populates="owner")

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    trade_type = Column(Enum(TradeType))
    volume = Column(Float)
    open_price = Column(Float)
    close_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    status = Column(Enum(TradeStatus), default=TradeStatus.OPEN)
    open_time = Column(DateTime)
    close_time = Column(DateTime, nullable=True)
    profit_loss = Column(Float, default=0.0)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="trades")

class TradeHistory(Base):
    __tablename__ = "trade_history"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String)
    trade_type = Column(Enum(TradeType))
    volume = Column(Float)
    open_price = Column(Float)
    close_price = Column(Float)
    open_time = Column(DateTime)
    close_time = Column(DateTime)
    profit_loss = Column(Float)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="trade_history")
