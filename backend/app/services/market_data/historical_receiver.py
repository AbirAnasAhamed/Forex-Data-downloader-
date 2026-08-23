import zmq
import json
import logging
import asyncio
from typing import List, Dict
from datetime import datetime
from backend.app.database.timescale_engine import SessionLocal
from backend.app.database.models.tick_data import TickData

logger = logging.getLogger("HistReceiver")

ZMQ_HIST_PUB_PORT = 7781

class HistoricalReceiver:
    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, "")
        self.is_running = False
        
    def start(self):
        """Start listening for historical chunks from the MT5 worker."""
        # Connect to MT5 engine in docker
        self.socket.connect(f"tcp://localhost:{ZMQ_HIST_PUB_PORT}")
        self.is_running = True
        asyncio.create_task(self._listen_loop())
        logger.info("Historical Receiver started listening on port 7781.")
        
    def stop(self):
        self.is_running = False
        self.socket.close()
        self.context.term()
        
    async def _listen_loop(self):
        while self.is_running:
            try:
                # Use polling to prevent blocking the asyncio loop forever
                event = self.socket.poll(timeout=100)
                if event == 0:
                    await asyncio.sleep(0.01)
                    continue
                    
                msg = self.socket.recv_string(flags=zmq.NOBLOCK)
                data = json.loads(msg)
                
                if data.get("status") == "chunk":
                    symbol = data.get("symbol")
                    chunk_data = data.get("data", [])
                    if chunk_data:
                        await self._save_chunk(symbol, chunk_data)
                elif data.get("status") == "complete":
                    logger.info(f"Historical sync complete for {data.get('symbol')}. Total ticks: {data.get('total_ticks')}")
                    
            except zmq.Again:
                pass
            except Exception as e:
                logger.error(f"Historical receiver error: {e}")
                await asyncio.sleep(1)

    async def _save_chunk(self, symbol: str, chunk_data: List[Dict]):
        """Save a large chunk of historical ticks to TimescaleDB."""
        # Run DB IO in a threadpool
        await asyncio.to_thread(self._sync_save, symbol, chunk_data)
        
    def _sync_save(self, symbol: str, chunk_data: List[Dict]):
        db = SessionLocal()
        try:
            mappings = []
            for t in chunk_data:
                mappings.append({
                    "time": datetime.fromtimestamp(t["time_msc"] / 1000.0),
                    "symbol": symbol,
                    "source": "mt5_hist",
                    "bid": t["bid"],
                    "ask": t["ask"],
                    "volume": t["volume"]
                })
            db.bulk_insert_mappings(TickData, mappings)
            db.commit()
            logger.info(f"Saved historical chunk of {len(mappings)} ticks for {symbol}.")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save historical chunk to DB: {e}")
        finally:
            db.close()

# Singleton instance
historical_receiver = HistoricalReceiver()
