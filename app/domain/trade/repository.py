import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.bot.models import Bot
from app.domain.trade.models import Trade


class TradeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        bot_id: uuid.UUID | None,
        symbol: str | None,
        status: str | None,
        page: int,
        per_page: int,
    ) -> tuple[list[Trade], int]:
        query = select(Trade).join(Bot, Bot.id == Trade.bot_id).where(Bot.user_id == user_id)
        count_query = select(Trade).join(Bot, Bot.id == Trade.bot_id).where(Bot.user_id == user_id)

        if bot_id:
            query = query.where(Trade.bot_id == bot_id)
            count_query = count_query.where(Trade.bot_id == bot_id)
        if symbol:
            query = query.where(Trade.symbol == symbol)
            count_query = count_query.where(Trade.symbol == symbol)
        if status:
            query = query.where(Trade.status == status)
            count_query = count_query.where(Trade.status == status)

        total_rows = (await self.db.execute(count_query)).scalars().all()
        total = len(total_rows)

        result = await self.db.execute(
            query.order_by(Trade.open_time.desc()).offset((page - 1) * per_page).limit(per_page)
        )
        return list(result.scalars().all()), total

    async def get_by_id_for_user(self, trade_id: uuid.UUID, user_id: uuid.UUID) -> Trade | None:
        result = await self.db.execute(
            select(Trade)
            .join(Bot, Bot.id == Trade.bot_id)
            .where(Trade.id == trade_id, Bot.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_closed(self, user_id: uuid.UUID, bot_id: uuid.UUID | None) -> list[Trade]:
        query = (
            select(Trade)
            .join(Bot, Bot.id == Trade.bot_id)
            .where(Bot.user_id == user_id, Trade.status == "closed")
        )
        if bot_id:
            query = query.where(Trade.bot_id == bot_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())
