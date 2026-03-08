import logging

from redis.asyncio import ConnectionPool, Redis
from redis.exceptions import ConnectionError as RedisConnectionError

from app.config import settings

_redis_client: Redis | None = None
logger = logging.getLogger(__name__)


async def init_redis() -> bool:
    global _redis_client
    pool = ConnectionPool.from_url(
        settings.REDIS_URL,
        max_connections=50,
        decode_responses=True,
    )
    _redis_client = Redis(connection_pool=pool)
    try:
        await _redis_client.ping()
        return True
    except RedisConnectionError as error:
        _redis_client = None
        if settings.REDIS_REQUIRED:
            raise
        logger.warning("Redis unavailable at startup (%s). Continuing without Redis features.", error)
        return False


async def get_redis() -> Redis:
    if _redis_client is None:
        raise RuntimeError("Redis not initialised — call init_redis() first")
    return _redis_client


async def close_redis():
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None


async def acquire_lock(key: str, ttl_seconds: int = 5) -> bool:
    redis = await get_redis()
    return bool(await redis.set(key, "1", nx=True, ex=ttl_seconds))


async def release_lock(key: str):
    redis = await get_redis()
    await redis.delete(key)


async def publish_event(channel: str, payload: str):
    redis = await get_redis()
    await redis.publish(channel, payload)
