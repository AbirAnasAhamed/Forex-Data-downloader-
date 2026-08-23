import polars as pl
import os
import logging
from typing import Optional

logger = logging.getLogger("FeatureEngineer")

class PolarsFeatureEngineer:
    """
    Tier-1 RAM-optimized Feature Engineering using Rust-based Polars.
    Converts raw tick data into OHLCV Time Bars and Quant features.
    """
    
    @staticmethod
    def ticks_to_time_bars(ticks_df: pl.DataFrame, timeframe: str = "1m") -> pl.DataFrame:
        """
        Convert Raw Ticks to OHLCV bars.
        Expected ticks_df columns: [time, bid, ask, volume]
        timeframe: Polars duration string (e.g., '1m', '5m', '1h')
        """
        # Create mid price
        df = ticks_df.with_columns(
            ((pl.col("bid") + pl.col("ask")) / 2.0).alias("price")
        )
        
        # Aggregate to OHLCV
        bars = (
            df.group_by_dynamic("time", every=timeframe)
            .agg([
                pl.col("price").first().alias("open"),
                pl.col("price").max().alias("high"),
                pl.col("price").min().alias("low"),
                pl.col("price").last().alias("close"),
                pl.col("volume").sum().alias("volume"),
                # Order Book Imbalance Proxy (simplified)
                (pl.col("ask").mean() - pl.col("bid").mean()).alias("spread_avg")
            ])
        )
        
        return bars
    
    @staticmethod
    def add_quant_features(bars_df: pl.DataFrame) -> pl.DataFrame:
        """
        Add standard algorithmic trading features.
        """
        # Basic Moving Averages
        bars_df = bars_df.with_columns([
            pl.col("close").rolling_mean(window_size=14).alias("sma_14"),
            pl.col("close").rolling_mean(window_size=50).alias("sma_50"),
        ])
        
        # Returns
        bars_df = bars_df.with_columns([
            (pl.col("close") / pl.col("close").shift(1) - 1).alias("return_1")
        ])
        
        # Drop nulls from rolling calculations
        bars_df = bars_df.drop_nulls()
        return bars_df
