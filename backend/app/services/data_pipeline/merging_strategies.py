import pandas as pd
import logging

logger = logging.getLogger("MergingStrategies")

class MergingStrategies:
    """
    Handles merging of L2 Snapshot Data and Live Tick Data.
    Assumes both DataFrames have a 'timestamp' column.
    """
    
    @staticmethod
    def merge_exact_match(df_primary: pd.DataFrame, df_secondary: pd.DataFrame, on_col: str = "timestamp") -> pd.DataFrame:
        """ 
        Merges two DataFrames keeping only exact timestamp matches. 
        """
        logger.info("Merging data using Exact Match strategy.")
        return pd.merge(df_primary, df_secondary, on=on_col, how='inner')

    @staticmethod
    def merge_forward_fill(df_primary: pd.DataFrame, df_secondary: pd.DataFrame, on_col: str = "timestamp") -> pd.DataFrame:
        """
        Merges two DataFrames and forward-fills missing values.
        Useful when L2 snapshots update slower than tick data (or vice versa).
        """
        logger.info("Merging data using Forward-Fill (ffill) strategy.")
        # Outer merge to keep all timestamps from both, sort, then ffill
        df_merged = pd.merge(df_primary, df_secondary, on=on_col, how='outer')
        df_merged = df_merged.sort_values(by=on_col).reset_index(drop=True)
        return df_merged.ffill()

    @staticmethod
    def merge_nearest_match(df_primary: pd.DataFrame, df_secondary: pd.DataFrame, on_col: str = "timestamp", tolerance=None) -> pd.DataFrame:
        """
        Merges two DataFrames aligning timestamps to the nearest match.
        Requires the 'timestamp' column to be numeric or datetime.
        """
        logger.info("Merging data using Nearest Match strategy.")
        
        # merge_asof requires the DataFrames to be sorted by the key
        df_primary_sorted = df_primary.sort_values(by=on_col)
        df_secondary_sorted = df_secondary.sort_values(by=on_col)
        
        return pd.merge_asof(
            df_primary_sorted, 
            df_secondary_sorted, 
            on=on_col, 
            direction='nearest',
            tolerance=tolerance
        )
