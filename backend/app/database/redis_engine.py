import os
import redis.asyncio as redis

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

class RedisEngine:
    def __init__(self):
        self.pool = redis.ConnectionPool(
            host=REDIS_HOST, 
            port=REDIS_PORT, 
            db=REDIS_DB, 
            decode_responses=True
        )
    
    def get_client(self):
        return redis.Redis(connection_pool=self.pool)

redis_engine = RedisEngine()

async def get_redis_client():
    client = redis_engine.get_client()
    try:
        yield client
    finally:
        await client.aclose()
