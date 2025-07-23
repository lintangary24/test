import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import List, Optional, Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Import from our new database module
from .database import SessionLocal, engine, create_db_and_tables, get_db
from .models import User, Trade, TradeHistory
from . import schemas, crud


class PriceUpdate(BaseModel):
    prices: Dict[str, float]


class PriceData(BaseModel):
    symbol: str
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    change: Optional[float] = None

# --- Configuration ---
SYMBOL = "CRYPTO:BTCUSD"
data_cache = {}  # Cache for data harga terakhir

# --- Dynamic Symbol Mapping ---
SYMBOL_MAPPINGS = {
    "CRYPTO:BTCUSD": {
        "display": "BTCUSD",
        "tradingView": "CRYPTO:BTCUSD",
        "description": "Bitcoin vs US Dollar",
        "name": "Bitcoin"
    }
}

# --- Security & Authentication ---
SECRET_KEY = "your-super-secret-key-that-is-long-and-secure"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# --- WebSocket Management ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast_json(self, json_data: dict):
        if json_data:
            for connection in self.active_connections:
                await connection.send_json(json_data)

manager = ConnectionManager()




# --- FastAPI Application ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Mengelola siklus hidup aplikasi: membuat tabel DB saat startup."""
    print("🚀 Memulai API Service...")
    create_db_and_tables()
    yield
    print("✅ API Service dimatikan.")



app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


# --- API Endpoints ---

@app.post("/internal/update-price")
async def update_price_from_scraper(price_data: PriceData):
    """
    Endpoint internal untuk menerima pembaruan harga dari layanan scraper.
    """
    symbol = price_data.symbol
    # Perbarui cache dengan data yang diterima
    data_cache[symbol] = price_data.dict()
    
    print(f"🔄 Menerima pembaruan harga untuk {symbol} dari scraper.")
    
    # Siarkan data yang diperbarui ke semua klien WebSocket yang terhubung
    await manager.broadcast_json(data_cache[symbol])
    
    return {"status": "ok", "symbol": symbol}


@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = crud.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/register", response_model=schemas.User)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user.password)
    return crud.create_user(db=db, user=user, hashed_password=hashed_password)


@app.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@app.get("/trades", response_model=List[schemas.Trade])
async def read_trades(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    trades = crud.get_trades(db, user_id=current_user.id, skip=skip, limit=limit)
    return trades


@app.post("/trades", response_model=schemas.Trade)
async def create_trade(
    trade: schemas.TradeCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        # The new crud function handles logic for market vs pending orders
        return crud.create_user_trade(db=db, trade=trade, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/trades/{trade_id}", response_model=schemas.TradeHistory)
async def close_trade_endpoint(
    trade_id: int,
    close_price: float,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    db_trade = crud.get_trade(db, trade_id=trade_id)
    if db_trade is None or db_trade.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    closed_trade_history = crud.close_trade(db, trade_id=trade_id, close_price=close_price)
    
    if closed_trade_history is None:
        raise HTTPException(status_code=400, detail="Could not close trade. It might not be an open trade.")
        
    return closed_trade_history


@app.post("/trades/close-all")
async def close_all_trades_endpoint(
    payload: PriceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Close all open trades for the current user."""
    result = crud.close_all_trades(db, user_id=current_user.id, prices=payload.prices)
    return result


@app.post("/trades/check-triggers", response_model=schemas.User)
async def check_triggers_endpoint(
    payload: PriceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    This endpoint is called periodically by the frontend to check for
    pending order triggers, SL/TP hits, and margin calls.
    It returns the updated user data, including equity.
    """
    crud.check_and_execute_trades(db, user_id=current_user.id, prices=payload.prices)
    # The user object might be stale after trades are executed, so refresh it
    db.refresh(current_user)
    return current_user


@app.get("/history", response_model=List[schemas.TradeHistory])
async def read_history(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    history = crud.get_history(db, user_id=current_user.id, skip=skip, limit=limit)
    return history


@app.get("/config")
async def get_config():
    """Get the main configured symbol"""
    return {"symbol": SYMBOL}


@app.get("/symbols")
async def get_symbols():
    """Get dynamic symbol mappings from backend"""
    return SYMBOL_MAPPINGS


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    print(f"🔗 Klien terhubung: {websocket.client.host}")
    
    # Send data for the configured symbol
    if SYMBOL in data_cache and data_cache[SYMBOL]:
        data_to_send = data_cache[SYMBOL].copy()
        # Always send the internal SYMBOL, not the display name
        data_to_send['symbol'] = SYMBOL
        await websocket.send_json(data_to_send)
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"🔌 Klien terputus: {websocket.client.host}")


# Mount the static directory to serve files like index.html, style.css, and api_client.js
# This must come AFTER all other API routes are defined.
app.mount("/", StaticFiles(directory="static", html=True), name="static")
