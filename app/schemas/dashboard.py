from __future__ import annotations

from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
    user_id: str
    balance: float
    equity: float
    margin: float
    daily_realized_pnl: float
    daily_unrealized_pnl: float
    bot_running: bool


class OpenTradeItem(BaseModel):
    id: int
    symbol: str
    side: str
    quantity: float
    entry_price: float
    opened_at: str


class ClosedTradeItem(BaseModel):
    id: int
    symbol: str
    side: str
    quantity: float
    entry_price: float
    close_price: float
    pnl: float
    close_reason: str
    opened_at: str
    closed_at: str


class DailyPnlResponse(BaseModel):
    user_id: str
    realized_pnl: float
    unrealized_pnl: float
    total_pnl: float


class NotificationItem(BaseModel):
    id: int
    event_type: str
    title: str
    message: str
    channel: str
    created_at: str
