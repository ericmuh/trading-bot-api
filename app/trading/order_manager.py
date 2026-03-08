import asyncio
import logging

from app.core.redis import acquire_lock, get_redis, release_lock
from app.trading.strategies.base import Action, TradeDecision

try:
    import MetaTrader5 as mt5
except ImportError:  # pragma: no cover
    mt5 = None

logger = logging.getLogger(__name__)


class OrderError(Exception):
    pass


class OrderManager:
    async def submit(
        self,
        decision: TradeDecision,
        bot_id: str,
        account_id: str,
        symbol: str,
        session,
        idempotency_key: str,
    ) -> dict | None:
        if decision.action == Action.HOLD:
            return None

        lock_key = f"trade:lock:{account_id}:{symbol}"
        idem_key = f"trade:idem:{idempotency_key}"
        redis = await get_redis()

        if await redis.exists(idem_key):
            logger.info("Duplicate signal suppressed: %s", idempotency_key)
            return None

        if not await acquire_lock(lock_key, ttl_seconds=5):
            logger.warning("Could not acquire order lock for %s/%s", account_id, symbol)
            return None

        try:
            tick = await session.get_tick(symbol)
            if not tick:
                raise OrderError(f"No tick for {symbol}")

            price = tick["ask"] if decision.action == Action.BUY else tick["bid"]
            point = await self._get_point(symbol)

            sl = (
                price - decision.stop_loss_pips * point
                if decision.action == Action.BUY
                else price + decision.stop_loss_pips * point
            )
            tp = (
                price + decision.take_profit_pips * point
                if decision.action == Action.BUY
                else price - decision.take_profit_pips * point
            )

            if mt5 is None:
                ticket = abs(hash(idempotency_key)) % 10_000_000
            else:
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": decision.lot_size,
                    "type": mt5.ORDER_TYPE_BUY if decision.action == Action.BUY else mt5.ORDER_TYPE_SELL,
                    "price": price,
                    "sl": round(sl, 5),
                    "tp": round(tp, 5),
                    "comment": f"bot:{bot_id[:8]}",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
                result = await asyncio.get_event_loop().run_in_executor(None, mt5.order_send, request)
                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    raise OrderError(f"MT5 order failed: {result.retcode} - {result.comment}")
                ticket = result.order

            await redis.setex(idem_key, 60, str(ticket))
            return {
                "ticket": ticket,
                "price": price,
                "sl": sl,
                "tp": tp,
                "idempotency_key": idempotency_key,
            }
        finally:
            await release_lock(lock_key)

    async def _get_point(self, symbol: str) -> float:
        if mt5 is None:
            return 0.0001
        info = await asyncio.get_event_loop().run_in_executor(None, mt5.symbol_info, symbol)
        return info.point if info else 0.00001
