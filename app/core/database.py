import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config
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


async def init_db():
    alembic_cfg = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(Path(__file__).resolve().parents[2] / "migrations"))
    await asyncio.to_thread(command.upgrade, alembic_cfg, "head")

    async with engine.begin() as conn:
        await conn.run_sync(lambda _: None)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
