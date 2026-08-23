import asyncio
import logging
from datetime import datetime
from backend.app.database.timescale_engine import SessionLocal
from backend.app.database.models.tick_data import TickData
from backend.app.database.models.l2_data import L2SnapshotData

logger = logging.getLogger("TickDBSaver")

class TickDBSaver:
    """
    Background worker that collects ticks from the live stream
    and bulk-inserts them into TimescaleDB to ensure high performance.
    """
    def __init__(self, batch_size=100, flush_interval=1.0):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.queue = asyncio.Queue()
        self.is_running = False
        self.worker_task = None

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.worker_task = asyncio.create_task(self._worker())
            logger.info("TickDBSaver background worker started.")

    def stop(self):
        self.is_running = False
        if self.worker_task:
            self.worker_task.cancel()
            self.worker_task = None
            logger.info("TickDBSaver background worker stopped.")

    async def add_tick(self, unified_tick: dict):
        """
        Adds a standardized tick to the queue for saving.
        """
        await self.queue.put(unified_tick)

    async def _worker(self):
        while self.is_running:
            batch_ticks = []
            batch_l2 = []
            
            try:
                # Wait for at least one item, then try to get more up to batch_size
                first_item = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                if first_item.get("type") == "tick":
                    batch_ticks.append(first_item)
                elif first_item.get("type") == "l2_snapshot":
                    batch_l2.append(first_item)
                
                while len(batch_ticks) + len(batch_l2) < self.batch_size:
                    try:
                        item = self.queue.get_nowait()
                        if item.get("type") == "tick":
                            batch_ticks.append(item)
                        elif item.get("type") == "l2_snapshot":
                            batch_l2.append(item)
                    except asyncio.QueueEmpty:
                        break
                        
                if batch_ticks or batch_l2:
                    await self._save_batches(batch_ticks, batch_l2)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in db_saver worker: {e}")

    async def _save_batches(self, batch_ticks: list, batch_l2: list):
        # Run DB IO in a threadpool to not block asyncio
        await asyncio.to_thread(self._sync_save, batch_ticks, batch_l2)
        
    def _sync_save(self, batch_ticks: list, batch_l2: list):
        db = SessionLocal()
        try:
            if batch_ticks:
                tick_mappings = []
                for t in batch_ticks:
                    tick_mappings.append({
                        "time": datetime.fromtimestamp(t["timestamp"] / 1000.0),
                        "symbol": t["symbol"],
                        "source": t["source"],
                        "bid": t["bid"],
                        "ask": t["ask"],
                        "volume": t["volume"]
                    })
                db.bulk_insert_mappings(TickData, tick_mappings)
                
            if batch_l2:
                l2_mappings = []
                for l in batch_l2:
                    l2_mappings.append({
                        "time": datetime.fromtimestamp(l["timestamp"] / 1000.0),
                        "symbol": l["symbol"],
                        "source": l["source"],
                        "bids": l["bids"],
                        "asks": l["asks"]
                    })
                db.bulk_insert_mappings(L2SnapshotData, l2_mappings)
                
            db.commit()
            logger.debug(f"Saved {len(batch_ticks)} ticks and {len(batch_l2)} L2 snapshots to DB.")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save batch to DB: {e}")
        finally:
            db.close()

# Singleton instance
tick_db_saver = TickDBSaver()
