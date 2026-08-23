import zmq
import zmq.asyncio
import asyncio
import json
import logging
import ssl

# logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("cTraderBridge")

ZMQ_SUB_PORT = 7778  # Receive commands from backend
ZMQ_PUB_PORT = 7779  # Publish ticks to backend

CTRADER_API_HOST = "live.openapi.ctradernet.com"
CTRADER_API_PORT = 5035

class CTraderOpenAPIClient:
    def __init__(self, client_id, secret, token, account_id):
        self.client_id = client_id
        self.secret = secret
        self.token = token
        self.account_id = account_id
        self.subscribed_symbol = None
        self.reader = None
        self.writer = None
        self.is_connected = False

    async def connect(self):
        logger.info(f"Connecting to cTrader Open API at {CTRADER_API_HOST}:{CTRADER_API_PORT}...")
        try:
            # cTrader Open API requires TLS
            ssl_context = ssl.create_default_context()
            self.reader, self.writer = await asyncio.open_connection(
                CTRADER_API_HOST, CTRADER_API_PORT, ssl=ssl_context
            )
            self.is_connected = True
            logger.info("TCP/TLS Connection established.")
            
            # Step 1: Send App Authentication Request (ProtoOAApplicationAuthReq)
            await self._authenticate_app()
            
            # Step 2: Send Account Authentication Request (ProtoOAAccountAuthReq)
            await self._authenticate_account()
            
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.is_connected = False
            return False

    async def _authenticate_app(self):
        logger.info("Authenticating application... (Protobuf integration pending)")
        # TODO: Construct ProtoOAApplicationAuthReq using protobuf and send
        pass

    async def _authenticate_account(self):
        logger.info("Authenticating account... (Protobuf integration pending)")
        # TODO: Construct ProtoOAAccountAuthReq using protobuf and send
        pass

    async def subscribe_symbol(self, symbol):
        self.subscribed_symbol = symbol
        logger.info(f"Subscribing to live ticks for {symbol}...")
        # TODO: Send ProtoOASubscribeSpotsReq
        pass

    async def read_messages(self, publish_callback):
        """
        Continuously read from the TCP stream, decode Protobuf messages,
        and pass tick data to the publish_callback.
        """
        while self.is_connected:
            try:
                # Typically length-prefixed protobuf messages
                # length_bytes = await self.reader.readexactly(4)
                # length = int.from_bytes(length_bytes, byteorder='big')
                # data = await self.reader.readexactly(length)
                
                # Mocking incoming data for now until protobuf compilation is done
                await asyncio.sleep(0.5) 
                
                # Mock tick
                import time
                current_time = time.time()
                tick = {
                    "type": "tick",
                    "symbol": self.subscribed_symbol or "UNKNOWN",
                    "time": int(current_time),
                    "time_msc": int(current_time * 1000),
                    "bid": 1.1000 + (current_time % 10) * 0.0001,
                    "ask": 1.1002 + (current_time % 10) * 0.0001,
                    "volume": 100
                }
                await publish_callback(tick)
                
                # Mock L2 Snapshot
                l2_snapshot = {
                    "type": "l2_snapshot",
                    "symbol": self.subscribed_symbol or "UNKNOWN",
                    "time_msc": int(current_time * 1000),
                    "bids": [{"price": tick["bid"] - i*0.0001, "volume": 100*i} for i in range(1, 6)],
                    "asks": [{"price": tick["ask"] + i*0.0001, "volume": 100*i} for i in range(1, 6)]
                }
                await publish_callback(l2_snapshot)
                
            except Exception as e:
                logger.error(f"Error reading message: {e}")
                self.is_connected = False
                break

    async def disconnect(self):
        self.is_connected = False
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        logger.info("Disconnected from cTrader Open API.")

async def main():
    context = zmq.asyncio.Context()
    
    # Subscriber socket for receiving login commands
    command_socket = context.socket(zmq.SUB)
    command_socket.bind(f"tcp://*:{ZMQ_SUB_PORT}")
    command_socket.setsockopt_string(zmq.SUBSCRIBE, "")
    
    # Publisher socket for sending live ticks
    tick_socket = context.socket(zmq.PUB)
    tick_socket.bind(f"tcp://*:{ZMQ_PUB_PORT}")
    
    logger.info("cTrader Bridge Engine Started. Waiting for commands...")
    
    active_client = None
    reader_task = None

    async def publish_tick(tick_data):
        await tick_socket.send_string(json.dumps(tick_data))

    while True:
        try:
            # Check for commands using asyncio
            msg = await command_socket.recv_string(flags=zmq.NOBLOCK)
            command_data = json.loads(msg)
            action = command_data.get("action")
            
            if action == "connect":
                if active_client:
                    await active_client.disconnect()
                    if reader_task:
                        reader_task.cancel()
                
                client_id = command_data.get("client_id")
                secret = command_data.get("secret")
                token = command_data.get("token")
                account_id = command_data.get("account_id")
                symbol = command_data.get("symbol")
                
                if not symbol:
                    logger.error("No symbol provided for connection.")
                    continue
                
                active_client = CTraderOpenAPIClient(client_id, secret, token, account_id)
                success = await active_client.connect()
                
                if success:
                    await active_client.subscribe_symbol(symbol)
                    reader_task = asyncio.create_task(active_client.read_messages(publish_tick))
                    
            elif action == "disconnect":
                if active_client:
                    await active_client.disconnect()
                    active_client = None
                if reader_task:
                    reader_task.cancel()
                    reader_task = None
                    
        except zmq.Again:
            # No new message
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            await asyncio.sleep(0.1)

if __name__ == "__main__":
    asyncio.run(main())
