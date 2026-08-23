import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.app.database.redis_engine import redis_engine

router = APIRouter()

from backend.app.core.cryptography import verify_token

@router.websocket("/ws/market/{symbol}")
async def market_data_websocket(websocket: WebSocket, symbol: str, token: str = None):
    """
    WebSocket endpoint that streams live market data to the frontend.
    It subscribes to the specific Redis Pub/Sub channel for the requested symbol.
    """
    await websocket.accept()
    
    # Secure Hedge Fund Standard: Validate Token
    if not token or verify_token(token) is None:
        await websocket.send_text("[ERROR] Unauthorized: Invalid or missing token")
        await websocket.close(code=1008)
        return
    
    # Get async redis client
    redis_client = redis_engine.get_client()
    pubsub = redis_client.pubsub()
    
    channel_name = f"live_ticks:{symbol}"
    await pubsub.subscribe(channel_name)
    
    try:
        while True:
            # Check if client sent any command (e.g. stop, ping)
            # using a small timeout so we don't block forever
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                if data.lower() == "ping":
                    await websocket.send_text("pong")
                elif data.lower() == "stop":
                    break
            except asyncio.TimeoutError:
                pass

            # Check for new messages from Redis Pub/Sub
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=0.1)
            if message and message['type'] == 'message':
                tick_data = message['data']
                # Send the standardized JSON data to the frontend
                await websocket.send_text(tick_data)

    except WebSocketDisconnect:
        print(f"Client disconnected from {symbol} stream.")
    except Exception as e:
        print(f"WebSocket error on {symbol}: {e}")
    finally:
        await pubsub.unsubscribe(channel_name)
        await pubsub.close()
