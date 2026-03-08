import uuid

from app.core.exceptions import AppException
from app.domain.trade.repository import TradeRepository


class TradeService:
    def __init__(self, trade_repo: TradeRepository):
        self.trade_repo = trade_repo

    async def list_trades(
        self,
        user_id: uuid.UUID,
        bot_id: uuid.UUID | None,
        symbol: str | None,
        status: str | None,
        page: int,
        per_page: int,
    ):
        return await self.trade_repo.list_by_user(user_id, bot_id, symbol, status, page, per_page)

    async def get_trade(self, user_id: uuid.UUID, trade_id: uuid.UUID):
        trade = await self.trade_repo.get_by_id_for_user(trade_id, user_id)
        if not trade:
            raise AppException("TRADE_NOT_FOUND", "Trade not found", 404)
        return trade

    async def get_stats(self, user_id: uuid.UUID, bot_id: uuid.UUID | None) -> dict:
        trades = await self.trade_repo.list_closed(user_id, bot_id)
        if not trades:
            return {"total_trades": 0, "win_rate": 0, "total_profit": 0, "avg_profit": 0}

        profits = [float(item.profit) for item in trades if item.profit is not None]
        if not profits:
            return {"total_trades": len(trades), "win_rate": 0, "total_profit": 0, "avg_profit": 0}

        wins = sum(1 for value in profits if value > 0)
        return {
            "total_trades": len(trades),
            "win_rate": round(wins / len(trades) * 100, 1),
            "total_profit": round(sum(profits), 2),
            "avg_profit": round(sum(profits) / len(profits), 2),
            "best_trade": max(profits),
            "worst_trade": min(profits),
        }
