import asyncio
from datetime import datetime, timezone
import logging

from app.core.database import AsyncSessionLocal
from app.core.redis import get_redis
from app.trading.session_manager import MT5ConnectionError, session_pool
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.tasks.bot_tasks.start_bot", queue="trading", bind=True, max_retries=3)
def start_bot(self, bot_id: str):
    logger.info("start_bot called for bot_id=%s", bot_id)


@celery_app.task(name="app.workers.tasks.bot_tasks.stop_bot", queue="trading", bind=True)
def stop_bot(self, bot_id: str):
    logger.info("stop_bot called for bot_id=%s", bot_id)
    asyncio.run(_stop_bot(bot_id))


@celery_app.task(name="app.workers.tasks.bot_tasks.check_bot_heartbeats", queue="admin")
def check_bot_heartbeats():
    logger.info("check_bot_heartbeats running")
    asyncio.run(_check_heartbeats())


@celery_app.task(name="app.workers.tasks.bot_tasks.sync_account_balances", queue="admin")
def sync_account_balances():
    logger.info("sync_account_balances running")
    asyncio.run(_sync_balances())


async def _stop_bot(bot_id: str):
    redis = await get_redis()
    await redis.set(f"bot:stop:{bot_id}", "1", ex=60)


async def _sync_balances():
    from app.domain.mt5_account.repository import MT5AccountRepository

    async with AsyncSessionLocal() as db:
        repo = MT5AccountRepository(db)
        accounts = await repo.list_all_active()
        for account in accounts:
            session = await session_pool.get(str(account.id))
            if not session or not session.is_connected:
                continue
            try:
                info = await session.get_account_info()
                account.balance = info["balance"]
                account.last_synced_at = datetime.now(timezone.utc)
                await db.flush()
                await db.commit()
            except Exception as error:
                logger.warning("Balance sync failed for %s: %s", account.id, error)


async def _check_heartbeats():
    from app.domain.bot.repository import BotRepository

    async with AsyncSessionLocal() as db:
        repo = BotRepository(db)
        running_bots = await repo.list_by_state("running")
        redis = await get_redis()

        for bot in running_bots:
            account_id = str(bot.account_id)
            alive = await redis.exists(f"mt5:heartbeat:{account_id}")
            if alive:
                await repo.reset_heartbeat_misses(bot.id)
                continue

            logger.warning("Dead session detected for account %s", account_id)
            misses = await repo.increment_heartbeat_miss(bot.id)
            session = await session_pool.get(account_id)
            if session:
                try:
                    await session.reconnect()
                    await repo.reset_heartbeat_misses(bot.id)
                except MT5ConnectionError:
                    if misses >= 3:
                        await repo.set_state(str(bot.id), "error")
            elif misses >= 3:
                await repo.set_state(str(bot.id), "error")

        await db.commit()
