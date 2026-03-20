from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine_options = {"echo": settings.DEBUG}
if not settings.database_url_async.startswith("sqlite"):
    engine_options.update(
        {
            "pool_size": settings.DATABASE_POOL_SIZE,
            "max_overflow": settings.DATABASE_MAX_OVERFLOW,
        }
    )

engine = create_async_engine(settings.database_url_async, **engine_options)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def _import_models() -> None:
    from app.domain.bot import models as _bot_models
    from app.domain.mt5_account import models as _mt5_models
    from app.domain.strategy import models as _strategy_models
    from app.domain.trade import models as _trade_models
    from app.domain.user import models as _user_models


async def init_db():
    async with engine.begin() as conn:
        if settings.database_url_async.startswith("sqlite"):
            _import_models()
            await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
