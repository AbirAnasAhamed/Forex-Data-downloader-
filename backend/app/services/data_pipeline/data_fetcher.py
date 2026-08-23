import pandas as pd
import logging
from backend.app.database.timescale_engine import engine
from datetime import datetime

logger = logging.getLogger("DataFetcher")

class DataFetcher:
    """
    Fetches data from TimescaleDB directly into Pandas DataFrames
    for exporting and merging strategies.
    """
    
    @staticmethod
    def fetch_ticks(symbol: str, start_time: datetime, end_time: datetime, source: str = None) -> pd.DataFrame:
        """
        Fetches live tick data for a given symbol and time range.
        Returns a Pandas DataFrame.
        """
        query = f"""
            SELECT time as timestamp, symbol, source, bid, ask, volume
            FROM tick_data
            WHERE symbol = %(symbol)s 
            AND time >= %(start_time)s 
            AND time <= %(end_time)s
        """
        params = {
            "symbol": symbol,
            "start_time": start_time,
            "end_time": end_time
        }
        
        if source:
            query += " AND source = %(source)s"
            params["source"] = source
            
        query += " ORDER BY time ASC;"
        
        try:
            logger.info(f"Fetching tick data for {symbol} from {start_time} to {end_time}...")
            df = pd.read_sql_query(query, engine, params=params)
            return df
        except Exception as e:
            logger.error(f"Failed to fetch tick data: {e}")
            return pd.DataFrame()
