from app.core.redis import close_redis


async def shutdown_services():
    await close_redis()
