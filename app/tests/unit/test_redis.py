import pytest

from app.core.redis import get_redis


@pytest.mark.asyncio
async def test_get_redis_before_init_raises():
    with pytest.raises(RuntimeError):
        await get_redis()
