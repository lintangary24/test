from sqlalchemy.orm import Session
from passlib.context import CryptContext
from typing import List, Optional
from datetime import datetime
from . import models, schemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate, hashed_password: str):
    db_user = models.User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        return False
    if not pwd_context.verify(password, user.hashed_password):
        return False
    return user

def get_trades(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Trade).filter(models.Trade.owner_id == user_id).offset(skip).limit(limit).all()

def get_trade(db: Session, trade_id: int):
    return db.query(models.Trade).filter(models.Trade.id == trade_id).first()

def create_user_trade(db: Session, trade: schemas.TradeCreate, user_id: int):
    db_trade = models.Trade(
        symbol=trade.symbol,
        trade_type=trade.trade_type,
        volume=trade.volume,
        open_price=trade.open_price,
        open_time=datetime.utcnow(),
        stop_loss=trade.stop_loss,
        take_profit=trade.take_profit,
        owner_id=user_id
    )
    db.add(db_trade)
    db.commit()
    db.refresh(db_trade)
    return db_trade

def close_trade(db: Session, trade_id: int, close_price: float):
    trade = get_trade(db, trade_id)
    if not trade or trade.status != models.TradeStatus.OPEN:
        return None
    
    trade.close_price = close_price
    trade.status = models.TradeStatus.CLOSED
    trade.close_time = datetime.utcnow()
    trade.profit_loss = (close_price - trade.open_price) * trade.volume if trade.trade_type == models.TradeType.BUY else (trade.open_price - close_price) * trade.volume
    
    # Create trade history
    history = models.TradeHistory(
        symbol=trade.symbol,
        trade_type=trade.trade_type,
        volume=trade.volume,
        open_price=trade.open_price,
        close_price=close_price,
        open_time=trade.open_time,
        close_time=trade.close_time,
        profit_loss=trade.profit_loss,
        owner_id=trade.owner_id
    )
    db.add(history)
    db.delete(trade)
    db.commit()
    return history

def get_history(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.TradeHistory).filter(models.TradeHistory.owner_id == user_id).offset(skip).limit(limit).all()

def close_all_trades(db: Session, user_id: int, prices: dict):
    trades = db.query(models.Trade).filter(
        models.Trade.owner_id == user_id,
        models.Trade.status == models.TradeStatus.OPEN
    ).all()
    
    closed_trades = []
    for trade in trades:
        if trade.symbol in prices:
            history = close_trade(db, trade.id, prices[trade.symbol])
            if history:
                closed_trades.append(history)
    
    return {"closed_trades": len(closed_trades)}

def check_and_execute_trades(db: Session, user_id: int, prices: dict):
    # This would contain logic for checking pending orders, SL/TP, etc.
    # For now, just return without doing anything
    pass
