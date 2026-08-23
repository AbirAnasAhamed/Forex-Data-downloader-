from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import datetime
import os
import logging
from backend.app.services.data_pipeline.data_fetcher import DataFetcher
from backend.app.services.data_pipeline.merging_strategies import MergingStrategies
from backend.app.services.data_pipeline.exporter import data_exporter

logger = logging.getLogger("DataExportAPI")

router = APIRouter()

class ExportRequest(BaseModel):
    symbol: str
    format: str # 'parquet', 'csv', 'feather'
    strategy: str # 'ffill', 'nearest', 'exact'
    start_time: datetime
    end_time: datetime

@router.post("/export")
async def export_data(req: ExportRequest):
    """
    Fetches historical tick and L2 data, merges them based on strategy, 
    and exports them in the requested format.
    """
    try:
        # Prevent OOM by limiting export date range to 30 days maximum
        delta = req.end_time - req.start_time
        if delta.days > 30:
            raise HTTPException(status_code=400, detail="Export range cannot exceed 30 days to prevent memory overload.")
        
        # Currently we only save tick data, not L2 in DB, so we just export raw ticks for now
        # until L2 saving logic is implemented in Phase 7.
        df_ticks = DataFetcher.fetch_ticks(req.symbol, req.start_time, req.end_time)
        
        if df_ticks.empty:
            raise HTTPException(status_code=404, detail="No data found for the given symbol and time range.")
        
        # Here we would normally merge with L2 Data using MergingStrategies
        # df_l2 = DataFetcher.fetch_l2(...)
        # if req.strategy == 'ffill':
        #     df_merged = MergingStrategies.merge_forward_fill(df_l2, df_ticks)
        df_merged = df_ticks # Fallback until L2 DB storage is ready
        
        filename_prefix = f"{req.symbol}_export_{int(datetime.now().timestamp())}"
        filepath = data_exporter.export(df_merged, filename_prefix, req.format)
        
        if not filepath or not os.path.exists(filepath):
            raise HTTPException(status_code=500, detail="Failed to generate export file.")
            
        return FileResponse(filepath, media_type='application/octet-stream', filename=os.path.basename(filepath))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during export: {e}")
        raise HTTPException(status_code=500, detail=str(e))
