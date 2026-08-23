import zmq.asyncio
import asyncio
import json
import logging
from backend.app.services.market_data.unified_formatter import UnifiedTickFormatter
from backend.app.database.redis_engine import redis_engine
from backend.app.services.market_data.db_saver import tick_db_saver

logger = logging.getLogger("LiveTickManager")

class EngineStreamer:
    """
    A base class for streaming data from a specific engine (MT5/cTrader)
    via ZeroMQ and pushing it to Redis Pub/Sub.
    """
    def __init__(self, engine_type: str, sub_port: int, pub_port: int, host: str = "localhost"):
        self.engine_type = engine_type
        self.cmd_port = sub_port  # Port to send commands TO the engine
        self.data_port = pub_port  # Port to receive data FROM the engine
        self.host = host
        
        self.context = None
        self.cmd_socket = None
        self.data_socket = None
        
        self.is_streaming = False
        self.stream_task = None
        self.redis_client = None

    def _init_sockets(self):
        if self.context is None:
            self.context = zmq.asyncio.Context()
            
            self.cmd_socket = self.context.socket(zmq.PUB)
            self.cmd_socket.connect(f"tcp://{self.host}:{self.cmd_port}")
            
            self.data_socket = self.context.socket(zmq.SUB)
            self.data_socket.connect(f"tcp://{self.host}:{self.data_port}")
            self.data_socket.setsockopt_string(zmq.SUBSCRIBE, "")
            
            self.redis_client = redis_engine.get_client()

    async def connect_engine(self, credentials: dict):
        self._init_sockets()
        command = {"action": "connect"}
        command.update(credentials)
        # Give ZMQ connection time to establish before sending command
        await asyncio.sleep(0.5) 
        await self.cmd_socket.send_string(json.dumps(command))
        logger.info(f"Sent connect command to {self.engine_type} engine.")

    async def disconnect_engine(self):
        command = {"action": "disconnect"}
        await self.cmd_socket.send_string(json.dumps(command))
        self.stop_streaming()
        logger.info(f"Sent disconnect command to {self.engine_type} engine.")

    async def start_streaming(self):
        if not self.is_streaming:
            self.is_streaming = True
            self.stream_task = asyncio.create_task(self._listen_and_publish())
            logger.info(f"Started streaming from {self.engine_type} engine.")

    def stop_streaming(self):
        self.is_streaming = False
        if self.stream_task:
            self.stream_task.cancel()
            self.stream_task = None

    async def _listen_and_publish(self):
        while self.is_streaming:
            try:
                # Wait for data from engine
                msg = await self.data_socket.recv_string(flags=zmq.NOBLOCK)
                raw_tick = json.loads(msg)
                
                # Normalize data format
                unified_tick = UnifiedTickFormatter.format_tick(self.engine_type, raw_tick)
                
                # Publish to Redis channel based on symbol
                # For L2 snapshots, we might want a different channel or same channel. We use same for simplicity.
                channel = f"live_ticks:{unified_tick['symbol']}"
                await self.redis_client.publish(channel, json.dumps(unified_tick))
                
                # Add to DB Saver queue for TimescaleDB insertion (only ticks, not huge L2 snapshots)
                if unified_tick.get("type") == "tick":
                    await tick_db_saver.add_tick(unified_tick)
                
                
            except zmq.Again:
                await asyncio.sleep(0.01)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error streaming from {self.engine_type}: {e}")
                await asyncio.sleep(0.01)


class LiveTickManager:
    """
    Factory pattern manager that allows dynamically switching between MT5 and cTrader engines.
    """
    def __init__(self):
        # MT5 uses 7776 for commands, 7777 for data
        self.mt5_streamer = EngineStreamer("mt5", 7776, 7777)
        # cTrader uses 7778 for commands, 7779 for data
        self.ctrader_streamer = EngineStreamer("ctrader", 7778, 7779)
        
        self.active_streamer = None
        
    def start(self):
        # Start background DB saver worker here, not in __init__, to ensure event loop exists
        tick_db_saver.start()

    async def switch_engine(self, engine_type: str, credentials: dict):
        # Stop current stream if running
        if self.active_streamer:
            await self.active_streamer.disconnect_engine()
            self.active_streamer = None
            
        # Select appropriate streamer
        if engine_type == "mt5":
            self.active_streamer = self.mt5_streamer
        elif engine_type == "ctrader":
            self.active_streamer = self.ctrader_streamer
        else:
            raise ValueError(f"Unknown engine type: {engine_type}")
            
        # Connect and start new stream
        await self.active_streamer.connect_engine(credentials)
        await self.active_streamer.start_streaming()

    async def disconnect(self):
        if self.active_streamer:
            await self.active_streamer.disconnect_engine()
            self.active_streamer = None
        tick_db_saver.stop()

# Singleton instance
live_tick_manager = LiveTickManager()
