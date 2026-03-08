import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.bot.models import Bot


class BotRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, bot_id: str | uuid.UUID) -> Bot | None:
        result = await self.db.execute(select(Bot).where(Bot.id == bot_id))
        return result.scalar_one_or_none()

    async def list_by_state(self, state: str) -> list[Bot]:
        result = await self.db.execute(select(Bot).where(Bot.state == state))
        return list(result.scalars().all())

    async def set_state(self, bot_id: str, state: str):
        bot = await self.get_by_id(bot_id)
        if bot:
            bot.state = state
            await self.db.flush()

    async def increment_heartbeat_miss(self, bot_id: uuid.UUID) -> int:
        bot = await self.get_by_id(bot_id)
        if not bot:
            return 0
        current = int((bot.worker_pod_id or "misses:0").split(":")[-1])
        current += 1
        bot.worker_pod_id = f"misses:{current}"
        await self.db.flush()
        return current

    async def reset_heartbeat_misses(self, bot_id: uuid.UUID):
        bot = await self.get_by_id(bot_id)
        if bot:
            bot.worker_pod_id = "misses:0"
            await self.db.flush()
