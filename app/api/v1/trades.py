from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.middleware.auth import get_current_user
from app.core.database import get_db
from app.domain.trade.repository import TradeRepository
from app.domain.trade.schemas import TradeResponse
from app.services.trade_service import TradeService

router = APIRouter()


def get_trade_service(db: AsyncSession = Depends(get_db)) -> TradeService:
    return TradeService(TradeRepository(db))


@router.get("")
async def list_trades(
    bot_id: UUID | None = None,
    symbol: str | None = None,
    status: str | None = None,
    page: int = 1,
    per_page: int = 20,
    current_user=Depends(get_current_user),
    service: TradeService = Depends(get_trade_service),
):
    trades, total = await service.list_trades(
        user_id=current_user.id,
        bot_id=bot_id,
        symbol=symbol,
        status=status,
        page=page,
        per_page=per_page,
    )
    return {
        "success": True,
        "data": [TradeResponse.model_validate(item) for item in trades],
        "meta": {"page": page, "per_page": per_page, "total": total},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/stats")
async def get_trade_stats(
    bot_id: UUID | None = None,
    current_user=Depends(get_current_user),
    service: TradeService = Depends(get_trade_service),
):
    stats = await service.get_stats(current_user.id, bot_id)
    return {
        "success": True,
        "data": stats,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/{trade_id}")
async def get_trade(
    trade_id: UUID,
    current_user=Depends(get_current_user),
    service: TradeService = Depends(get_trade_service),
):
    trade = await service.get_trade(current_user.id, trade_id)
    return {
        "success": True,
        "data": TradeResponse.model_validate(trade),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
