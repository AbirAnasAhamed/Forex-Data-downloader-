from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.app.services.market_data.live_tick_manager import live_tick_manager
import logging

logger = logging.getLogger("EngineControlAPI")

router = APIRouter()

class ConnectRequest(BaseModel):
    engine_type: str # 'mt5' or 'ctrader'
    symbol: str
    server: Optional[str] = None
    login: Optional[str] = None
    password: Optional[str] = None
    client_id: Optional[str] = None
    secret: Optional[str] = None
    token: Optional[str] = None
    account_id: Optional[str] = None

@router.post("/connect")
async def connect_engine(req: ConnectRequest):
    """
    Connects to the specified engine (MT5 or cTrader) and starts streaming live data.
    """
    try:
        credentials = req.dict(exclude_none=True)
        await live_tick_manager.switch_engine(req.engine_type, credentials)
        return {"status": "success", "message": f"Successfully connected to {req.engine_type} and streaming {req.symbol}"}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error connecting to engine: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during engine connection")

@router.post("/disconnect")
async def disconnect_engine():
    """
    Disconnects the active engine and stops streaming.
    """
    try:
        await live_tick_manager.disconnect()
        return {"status": "success", "message": "Engine disconnected successfully."}
    except Exception as e:
        logger.error(f"Error disconnecting from engine: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during disconnect")
