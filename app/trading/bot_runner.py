import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import func, select

from app.core.redis import get_redis
from app.domain.trade.models import Trade
from app.services.ai_service import AIService
from app.trading.order_manager import OrderManager
from app.trading.risk_manager import RiskBreachError, RiskManager
from app.trading.session_manager import MT5ConnectionError, session_pool
from app.trading.strategies import get_strategy

logger = logging.getLogger(__name__)


class BotRunner:
    def __init__(self, bot_config: dict, db_session):
        self.bot = bot_config
        self.db = db_session
        self.running = False
        self.strategy = get_strategy(bot_config["strategy_class_name"], bot_config.get("params", {}))
        self.risk_manager = RiskManager(bot_config)
        self.order_manager = OrderManager()
        self.ai_service = AIService()

    async def run(self):
        self.running = True
        account_id = str(self.bot["account_id"])
        bot_id = str(self.bot["id"])
        symbol = self.bot["symbol"]
        timeframe = self.bot["timeframe"]
        poll_interval = int(self.bot.get("poll_interval", 5))

        session = await session_pool.acquire(account_id, self.bot["session_config"])
        asyncio.create_task(session.start_heartbeat())

        while self.running:
            try:
                await self._publish_heartbeat(bot_id)

                tick = await session.get_tick(symbol)
                ohlcv = await session.get_ohlcv(symbol, timeframe, count=220)

                signal = await self.ai_service.get_signal(ohlcv, self.bot["strategy_id"])
                if signal.confidence < float(self.bot.get("min_ai_confidence", 0.65)):
                    await asyncio.sleep(poll_interval)
                    continue

                decision = await self.strategy.evaluate(tick or {}, ohlcv, signal)

                account_info = await session.get_account_info()
                open_count = await self._count_open_trades(bot_id)
                await self.risk_manager.validate(
                    decision,
                    open_count,
                    account_info,
                    float(self.bot.get("day_start_balance", account_info.get("balance", 1.0))),
                )

                if decision.action.value != "HOLD":
                    idempotency_key = f"{bot_id}:{signal.timestamp.isoformat()}"
                    order = await self.order_manager.submit(
                        decision,
                        bot_id,
                        account_id,
                        symbol,
                        session,
                        idempotency_key,
                    )
                    if order:
                        await self._record_trade(order, decision, signal)
                        await self.db.commit()

                stop_flag = await self._stop_requested(bot_id)
                if stop_flag:
                    await self.stop()

                await asyncio.sleep(poll_interval)
            except MT5ConnectionError:
                await session.reconnect()
            except RiskBreachError as error:
                logger.warning("Bot %s risk breach [%s] %s", bot_id, error.code, error.message)
                if error.code == "MAX_DRAWDOWN":
                    await self.stop()
            except Exception as error:
                logger.error("Bot %s unexpected error: %s", bot_id, error, exc_info=True)
                await asyncio.sleep(5)

    async def stop(self):
        self.running = False

    async def _publish_heartbeat(self, bot_id: str):
        redis = await get_redis()
        await redis.setex(f"bot:heartbeat:{bot_id}", 30, datetime.now(timezone.utc).isoformat())

    async def _stop_requested(self, bot_id: str) -> bool:
        redis = await get_redis()
        return bool(await redis.exists(f"bot:stop:{bot_id}"))

    async def _count_open_trades(self, bot_id: str) -> int:
        result = await self.db.execute(select(func.count()).where(Trade.bot_id == bot_id, Trade.status == "open"))
        return int(result.scalar() or 0)

    async def _record_trade(self, order: dict, decision, signal):
        trade = Trade(
            bot_id=self.bot["id"],
            account_id=self.bot["account_id"],
            mt5_ticket=order["ticket"],
            symbol=self.bot["symbol"],
            direction=decision.action.value,
            lot_size=decision.lot_size,
            open_price=order["price"],
            stop_loss=order["sl"],
            take_profit=order["tp"],
            ai_confidence=signal.confidence,
            status="open",
            idempotency_key=order["idempotency_key"],
        )
        self.db.add(trade)
        await self.db.flush()
