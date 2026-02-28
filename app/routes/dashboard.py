from __future__ import annotations

from fastapi import APIRouter, Query

from app.db import store
from app.schemas.dashboard import (
    ClosedTradeItem,
    DailyPnlResponse,
    DashboardSummaryResponse,
    NotificationItem,
    OpenTradeItem,
)
from app.services.dashboard_service import DashboardService

router = APIRouter(tags=["portfolio"])
dashboard_service = DashboardService()


@router.get("/summary", response_model=DashboardSummaryResponse)
def dashboard_summary(user_id: str = Query(..., min_length=1)) -> DashboardSummaryResponse:
    return DashboardSummaryResponse(**dashboard_service.summary(user_id))


@router.get("/trades/open", response_model=list[OpenTradeItem])
def open_trades(user_id: str = Query(..., min_length=1)) -> list[OpenTradeItem]:
    rows = store.get_open_trades(user_id)
    return [OpenTradeItem(**row) for row in rows]


@router.get("/trades/closed", response_model=list[ClosedTradeItem])
def closed_trades(
    user_id: str = Query(..., min_length=1),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[ClosedTradeItem]:
    rows = store.get_closed_trades(user_id, limit=limit)
    return [ClosedTradeItem(**row) for row in rows]


@router.get("/pnl/daily", response_model=DailyPnlResponse)
def daily_pnl(user_id: str = Query(..., min_length=1)) -> DailyPnlResponse:
    prices = dashboard_service.current_prices(user_id)
    realized = store.get_realized_pnl_today(user_id)
    unrealized = store.get_unrealized_pnl(user_id, prices)
    return DailyPnlResponse(
        user_id=user_id,
        realized_pnl=round(realized, 6),
        unrealized_pnl=round(unrealized, 6),
        total_pnl=round(realized + unrealized, 6),
    )


@router.get("/notifications", response_model=list[NotificationItem])
def notifications(
    user_id: str = Query(..., min_length=1),
    channel: str = Query(default="in_app", pattern="^(in_app|email)$"),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[NotificationItem]:
    rows = store.list_notifications(user_id=user_id, channel=channel, limit=limit)
    return [NotificationItem(**row) for row in rows]
