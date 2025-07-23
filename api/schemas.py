from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from .models import TradeType, TradeStatus

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    balance: float
    is_active: bool
    
    class Config:
        from_attributes = True

class TradeBase(BaseModel):
    symbol: str
    trade_type: TradeType
    volume: float
    open_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

class TradeCreate(TradeBase):
    pass

class Trade(TradeBase):
    id: int
    close_price: Optional[float] = None
    status: TradeStatus
    open_time: datetime
    close_time: Optional[datetime] = None
    profit_loss: float
    owner_id: int
    
    class Config:
        from_attributes = True

class TradeHistory(BaseModel):
    id: int
    symbol: str
    trade_type: TradeType
    volume: float
    open_price: float
    close_price: float
    open_time: datetime
    close_time: datetime
    profit_loss: float
    owner_id: int
    
    class Config:
        from_attributes = True

class PriceUpdate(BaseModel):
    prices: dict[str, float]

class PriceData(BaseModel):
    symbol: str
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    change: Optional[float] = None
