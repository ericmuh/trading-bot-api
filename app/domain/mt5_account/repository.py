import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.mt5_account.models import MT5Account


class MT5AccountRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **kwargs) -> MT5Account:
        account = MT5Account(**kwargs)
        self.db.add(account)
        try:
            await self.db.flush()
        except IntegrityError:
            await self.db.rollback()
            raise
        await self.db.refresh(account)
        return account

    async def list_by_user(self, user_id: uuid.UUID) -> list[MT5Account]:
        result = await self.db.execute(
            select(MT5Account).where(MT5Account.user_id == user_id, MT5Account.is_active.is_(True))
        )
        return list(result.scalars().all())

    async def list_all_active(self) -> list[MT5Account]:
        result = await self.db.execute(select(MT5Account).where(MT5Account.is_active.is_(True)))
        return list(result.scalars().all())

    async def get_by_id(self, account_id: uuid.UUID, user_id: uuid.UUID) -> MT5Account | None:
        result = await self.db.execute(
            select(MT5Account).where(MT5Account.id == account_id, MT5Account.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_any_user(self, account_id: uuid.UUID) -> MT5Account | None:
        result = await self.db.execute(select(MT5Account).where(MT5Account.id == account_id))
        return result.scalar_one_or_none()

    async def soft_delete(self, account: MT5Account):
        account.is_active = False
        await self.db.flush()
