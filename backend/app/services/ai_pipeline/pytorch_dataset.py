import torch
from torch.utils.data import IterableDataset
import polars as pl
from typing import Iterator, Tuple
import logging
from backend.app.services.ai_pipeline.data_lake import ParquetDataLake

logger = logging.getLogger("PyTorchDataset")

class ForexIterableDataset(IterableDataset):
    """
    Tier-1 PyTorch IterableDataset for Deep Learning models (LSTM, Transformer).
    Uses Polars LazyFrame to stream data directly from Parquet files on disk 
    into PyTorch Tensors, completely bypassing RAM limits.
    """
    def __init__(self, symbol: str, timeframe: str = "1m", sequence_length: int = 60, batch_size: int = 10000):
        super().__init__()
        self.symbol = symbol
        self.timeframe = timeframe
        self.sequence_length = sequence_length
        self.batch_size = batch_size
        
        # We only keep the LazyFrame reference in memory, not the data
        try:
            self.lazy_df = ParquetDataLake.scan_symbol_data(symbol, timeframe)
        except FileNotFoundError:
            logger.error(f"Cannot initialize dataset, no data lake for {symbol}")
            self.lazy_df = None

    def __iter__(self) -> Iterator[Tuple[torch.Tensor, torch.Tensor]]:
        """
        Yields (X, y) pairs where X is a sequence of historical features, 
        and y is the next time step's target (e.g., return).
        """
        if self.lazy_df is None:
            return
            
        # We process the data in chunks (batches) using Polars streaming capability
        # to ensure we never load the full dataset into RAM.
        try:
            # We select features we want to feed the AI
            feature_cols = ["open", "high", "low", "close", "volume", "spread_avg", "sma_14", "sma_50"]
            
            # Use fetch to lazily stream chunks of rows
            # Note: For sequence models, we need a sliding window. In a true production 
            # environment, we would use a rolling window function on the chunk.
            # Here we demonstrate the zero-copy streaming architecture.
            
            current_offset = 0
            while True:
                # Load a slice of the lazy frame into memory
                chunk_df = self.lazy_df.slice(current_offset, self.batch_size).collect()
                
                if len(chunk_df) <= self.sequence_length:
                    break
                    
                # Extract numerical features as numpy array, then to tensor
                # We drop rows with nulls (like rolling averages initial rows)
                clean_df = chunk_df.drop_nulls()
                if len(clean_df) <= self.sequence_length:
                    current_offset += self.batch_size
                    continue
                    
                features_np = clean_df.select(feature_cols).to_numpy()
                tensor_data = torch.FloatTensor(features_np)
                
                # Yield sliding windows
                for i in range(len(tensor_data) - self.sequence_length):
                    x = tensor_data[i : i + self.sequence_length]
                    # Simple target: predicting the next close price change (return)
                    # This is just an example target.
                    y_close = tensor_data[i + self.sequence_length, 3] # 'close' is index 3
                    y_prev_close = tensor_data[i + self.sequence_length - 1, 3]
                    y = (y_close / y_prev_close) - 1.0
                    
                    yield x, y.unsqueeze(0)
                
                current_offset += self.batch_size
                
        except Exception as e:
            logger.error(f"Error streaming data to PyTorch: {e}")
            raise
