import uuid

from app.core.exceptions import AppException
from app.domain.bot.repository import BotRepository
from app.domain.bot.schemas import BotCreate
from app.workers.tasks.bot_tasks import start_bot as start_bot_task
from app.workers.tasks.bot_tasks import stop_bot as stop_bot_task


class BotService:
    def __init__(self, bot_repo: BotRepository):
        self.bot_repo = bot_repo

    async def list_bots(self, user_id: uuid.UUID):
        return await self.bot_repo.list_by_user(user_id)

    async def create_bot(self, user_id: uuid.UUID, payload: BotCreate):
        return await self.bot_repo.create(
            user_id=user_id,
            account_id=payload.account_id,
            strategy_id=payload.strategy_id,
            name=payload.name,
            symbol=payload.symbol,
            timeframe=payload.timeframe,
            state="created",
            lot_size=payload.lot_size,
            max_trades=payload.max_trades,
            max_drawdown_pct=payload.max_drawdown_pct,
            min_ai_confidence=payload.min_ai_confidence,
            worker_pod_id="misses:0",
        )

    async def get_bot(self, user_id: uuid.UUID, bot_id: uuid.UUID):
        bot = await self.bot_repo.get_by_id_for_user(bot_id, user_id)
        if not bot:
            raise AppException("BOT_NOT_FOUND", "Bot not found", 404)
        return bot

    async def update_bot(self, user_id: uuid.UUID, bot_id: uuid.UUID, updates: dict):
        bot = await self.get_bot(user_id, bot_id)
        if bot.state == "running":
            raise AppException("BOT_RUNNING", "Stop bot before updating", 409)
        return await self.bot_repo.update(bot, updates)

    async def delete_bot(self, user_id: uuid.UUID, bot_id: uuid.UUID):
        bot = await self.get_bot(user_id, bot_id)
        if bot.state == "running":
            raise AppException("BOT_RUNNING", "Stop bot before deleting", 409)
        await self.bot_repo.delete(bot)

    async def start_bot(self, user_id: uuid.UUID, bot_id: uuid.UUID):
        bot = await self.get_bot(user_id, bot_id)
        if bot.state == "running":
            raise AppException("BOT_ALREADY_RUNNING", "Bot is already running", 409)
        await self.bot_repo.set_state(str(bot.id), "starting")
        start_bot_task.delay(str(bot.id))

    async def stop_bot(self, user_id: uuid.UUID, bot_id: uuid.UUID):
        bot = await self.get_bot(user_id, bot_id)
        await self.bot_repo.set_state(str(bot.id), "stopping")
        stop_bot_task.delay(str(bot.id))

    async def pause_bot(self, user_id: uuid.UUID, bot_id: uuid.UUID):
        bot = await self.get_bot(user_id, bot_id)
        if bot.state != "running":
            raise AppException("BOT_NOT_RUNNING", "Only running bots can be paused", 409)
        await self.bot_repo.set_state(str(bot.id), "paused")

