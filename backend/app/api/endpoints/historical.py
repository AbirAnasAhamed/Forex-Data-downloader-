import zmq
import json
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import logging
from datetime import datetime, timedelta
import asyncio
import polars as pl

from backend.app.services.data_pipeline.data_fetcher import DataFetcher
from backend.app.services.ai_pipeline.feature_engineer import PolarsFeatureEngineer
from backend.app.services.ai_pipeline.data_lake import ParquetDataLake
from backend.app.services.ai_pipeline.pytorch_dataset import ForexIterableDataset

logger = logging.getLogger("HistoricalAPI")

router = APIRouter()
ZMQ_HIST_SUB_PORT = 7780  # Port where historical_worker.py is listening

class DownloadRequest(BaseModel):
    symbol: str
    server: str
    login: str
    password: str
    start_time: datetime
    end_time: datetime

class FeatureRequest(BaseModel):
    symbol: str
    timeframe: str = "1m"

def send_download_command(req: DownloadRequest):
    """Sends a ZMQ command to the MT5 Docker container to start historical chunking."""
    try:
        context = zmq.Context()
        socket = context.socket(zmq.PUB)
        socket.connect(f"tcp://localhost:{ZMQ_HIST_SUB_PORT}")
        
        # Give ZMQ time to connect
        import time
        time.sleep(0.5)
        
        command = {
            "action": "fetch",
            "symbol": req.symbol,
            "server": req.server,
            "login": req.login,
            "password": req.password,
            "start_time": int(req.start_time.timestamp() * 1000),
            "end_time": int(req.end_time.timestamp() * 1000)
        }
        
        socket.send_string(json.dumps(command))
        logger.info(f"Sent historical download command for {req.symbol}")
        
        # Give ZMQ background thread time to flush the message before closing
        time.sleep(0.5)
        
        socket.close()
        context.term()
    except Exception as e:
        logger.error(f"Failed to send download command: {e}")

@router.post("/download")
async def trigger_historical_download(req: DownloadRequest, background_tasks: BackgroundTasks):
    """
    Triggers the background chunked download process.
    """
    try:
        background_tasks.add_task(send_download_command, req)
        return {"status": "success", "message": f"Historical download initiated for {req.symbol}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def run_ai_pipeline(symbol: str, timeframe: str):
    """Background task to generate features, save to Data Lake, and run PyTorch dataset."""
    try:
        # 1. Fetch raw ticks (last 30 days for this demo to avoid taking too long)
        end_time = datetime.now()
        start_time = end_time - timedelta(days=30)
        logger.info(f"AI Pipeline: Fetching raw ticks for {symbol}...")
        df_pandas = DataFetcher.fetch_ticks(symbol, start_time, end_time)
        
        if df_pandas.empty:
            logger.warning("AI Pipeline: No data found in TimescaleDB!")
            return
            
        # 2. Convert to Polars and engineer features
        logger.info("AI Pipeline: Engineering features using Polars...")
        df_polars = pl.from_pandas(df_pandas)
        bars = PolarsFeatureEngineer.ticks_to_time_bars(df_polars, timeframe=timeframe)
        features = PolarsFeatureEngineer.add_quant_features(bars)
        
        # 3. Save to Parquet Data Lake
        logger.info("AI Pipeline: Saving features to Parquet Data Lake...")
        ParquetDataLake.save_features(symbol, features, timeframe)
        
        # 4. Initialize PyTorch Dataset (Zero-Copy)
        logger.info("AI Pipeline: Initializing PyTorch Memory-Mapped Dataset...")
        dataset = ForexIterableDataset(symbol, timeframe)
        # Fetch just one batch to test
        for x, y in dataset:
            logger.info(f"AI Pipeline: PyTorch successfully loaded batch shape X: {x.shape}, y: {y.shape}")
            break
            
        logger.info("AI Pipeline: Training initialization complete.")
    except Exception as e:
        logger.error(f"AI Pipeline Error: {e}")

@router.post("/train_ai")
async def trigger_ai_training(req: FeatureRequest, background_tasks: BackgroundTasks):
    """
    Triggers the real AI training pipeline.
    """
    background_tasks.add_task(run_ai_pipeline, req.symbol, req.timeframe)
    return {"status": "success", "message": f"AI Pipeline started on {req.symbol} ({req.timeframe}). Generating features & streaming Parquet Data Lake."}
