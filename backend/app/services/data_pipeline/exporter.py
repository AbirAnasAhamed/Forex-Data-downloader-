import pandas as pd
import logging
import os

logger = logging.getLogger("DataExporter")

class DataExporter:
    """
    Handles high-performance exporting of Pandas DataFrames into various formats.
    """
    def __init__(self, export_dir: str = "./exports"):
        self.export_dir = export_dir
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)

    def export(self, df: pd.DataFrame, filename_prefix: str, format_type: str) -> str:
        """
        Exports the DataFrame to the specified format.
        Supported formats: 'parquet', 'csv', 'feather'
        """
        if df is None or df.empty:
            logger.warning("Attempted to export an empty DataFrame.")
            return ""

        format_type = format_type.lower()
        filepath = os.path.join(self.export_dir, f"{filename_prefix}.{format_type}")
        
        try:
            if format_type == "parquet":
                # Parquet is highly compressed and fast to read/write for big data
                df.to_parquet(filepath, engine='pyarrow', index=False)
            elif format_type == "csv":
                # CSV is standard but slower and takes more disk space
                df.to_csv(filepath, index=False)
            elif format_type == "feather":
                # Feather is optimized for extremely fast read/write in Python/R
                # Requires a default index, so we reset it just in case
                df = df.reset_index(drop=True)
                df.to_feather(filepath)
            else:
                raise ValueError(f"Unsupported export format: {format_type}")
            
            logger.info(f"Successfully exported data to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to export data to {format_type}: {e}")
            raise e

# Singleton instance
data_exporter = DataExporter()
