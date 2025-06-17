import redis.asyncio as aioredis
from typing import Optional, Any
import json
from app.core.config import settings

# Global Redis connection
redis_client: Optional[aioredis.Redis] = None

async def init_redis():
    """Initialize Redis connection"""
    global redis_client
    redis_client = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )

async def get_redis() -> aioredis.Redis:
    """Get Redis client"""
    return redis_client

async def cache_set(key: str, value: Any, expire: int = 3600):
    """Set cache value"""
    if redis_client:
        serialized_value = json.dumps(value, default=str)
        await redis_client.set(key, serialized_value, ex=expire)

async def cache_get(key: str) -> Optional[Any]:
    """Get cache value"""
    if redis_client:
        value = await redis_client.get(key)
        if value:
            return json.loads(value)
    return None

async def cache_delete(key: str):
    """Delete cache value"""
    if redis_client:
        await redis_client.delete(key)