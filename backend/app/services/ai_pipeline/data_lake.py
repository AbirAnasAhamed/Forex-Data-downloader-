import os
import polars as pl
import logging
from datetime import datetime

logger = logging.getLogger("DataLake")

# Base directory for the data lake (can be overridden by env vars in a real system)
DATA_LAKE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data_lake")

class ParquetDataLake:
    """
    Manages the Tier-1 Hedge Fund Data Lake.
    Stores OHLCV and Quant features in partitioned .parquet files for extremely fast
    PyTorch memory-mapped loading.
    """
    
    @staticmethod
    def ensure_dir(symbol: str) -> str:
        symbol_dir = os.path.join(DATA_LAKE_DIR, symbol)
        if not os.path.exists(symbol_dir):
            os.makedirs(symbol_dir)
        return symbol_dir

    @staticmethod
    def save_features(symbol: str, df: pl.DataFrame, timeframe: str = "1m"):
        """
        Saves a Polars DataFrame of features into a partitioned Parquet file.
        Partitioning by symbol and timeframe.
        """
        try:
            symbol_dir = ParquetDataLake.ensure_dir(symbol)
            # Create a unique filename based on the current timestamp to avoid overwrites
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"{symbol}_{timeframe}_{timestamp_str}.parquet"
            file_path = os.path.join(symbol_dir, file_name)
            
            # Save using pyarrow backend for highest compatibility and compression
            df.write_parquet(file_path, compression="snappy")
            logger.info(f"DataLake: Saved {len(df)} rows to {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"DataLake: Error saving features to Parquet: {e}")
            raise
            
    @staticmethod
    def scan_symbol_data(symbol: str, timeframe: str = "1m") -> pl.LazyFrame:
        """
        Lazily scans all parquet files for a specific symbol and timeframe.
        Does NOT load data into RAM until collected, perfect for PyTorch datasets.
        """
        symbol_dir = os.path.join(DATA_LAKE_DIR, symbol)
        if not os.path.exists(symbol_dir):
            raise FileNotFoundError(f"No Data Lake directory found for symbol {symbol}")
            
        file_pattern = os.path.join(symbol_dir, f"{symbol}_{timeframe}_*.parquet")
        
        # Lazy frame prevents RAM overload
        lazy_df = pl.scan_parquet(file_pattern)
        return lazy_df
