from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BotCreate(BaseModel):
    account_id: UUID
    strategy_id: UUID
    strategy_class_name: str = "ScalpingStrategy"
    name: str
    symbol: str
    timeframe: str
    lot_size: float = Field(default=0.01, ge=0.01)
    max_trades: int = 5
    max_drawdown_pct: float = 5.0
    min_ai_confidence: float = 0.65


class BotUpdate(BaseModel):
    name: str | None = None
    symbol: str | None = None
    timeframe: str | None = None
    lot_size: float | None = Field(default=None, ge=0.01)
    max_trades: int | None = None
    max_drawdown_pct: float | None = None
    min_ai_confidence: float | None = None


class BotResponse(BaseModel):
    id: UUID
    user_id: UUID
    account_id: UUID
    strategy_id: UUID
    name: str
    symbol: str
    timeframe: str
    state: str
    lot_size: float
    max_trades: int
    max_drawdown_pct: float
    min_ai_confidence: float
    created_at: datetime

    model_config = {"from_attributes": True}
