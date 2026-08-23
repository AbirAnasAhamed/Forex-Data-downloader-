import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Import routers and initializers
from backend.app.api.websockets.market_stream import router as ws_router
from backend.app.api.endpoints.engine_control import router as engine_router
from backend.app.api.endpoints.data_export import router as export_router
from backend.app.api.endpoints.config import router as config_router
from backend.app.database.timescale_engine import init_timescale_extensions
from backend.app.database.models.tick_data import init_hypertable
from backend.app.database.models.l2_data import init_l2_hypertable
from backend.app.api.endpoints.historical import router as historical_router
from backend.app.services.market_data.historical_receiver import historical_receiver

app = FastAPI(title="Forex Hybrid Data Pipeline", version="1.0.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logging.info("Starting up FastAPI application...")
    # Initialize TimescaleDB extensions and hypertable
    try:
        from backend.app.database.models.user import init_users_table
        init_timescale_extensions()
        init_hypertable()
        init_l2_hypertable()
        init_users_table()
        # Start historical ZMQ receiver
        historical_receiver.start()
        # Start live tick manager (moved from import time)
        from backend.app.services.market_data.live_tick_manager import live_tick_manager
        live_tick_manager.start()
    except Exception as e:
        logging.error(f"Failed to initialize Database: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    logging.info("Shutting down FastAPI application...")
    from backend.app.services.market_data.live_tick_manager import live_tick_manager
    await live_tick_manager.disconnect()

# Include Routers
from fastapi import Depends
from backend.app.api.endpoints.auth import router as auth_router, get_current_user

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(ws_router, tags=["websockets"]) # WS protected inside the endpoint
app.include_router(engine_router, prefix="/api/engine", tags=["engine"], dependencies=[Depends(get_current_user)])
app.include_router(export_router, prefix="/api/data", tags=["export"], dependencies=[Depends(get_current_user)])
app.include_router(config_router, prefix="/api/config", tags=["config"], dependencies=[Depends(get_current_user)])
app.include_router(historical_router, prefix="/api/historical", tags=["historical"], dependencies=[Depends(get_current_user)])

if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
