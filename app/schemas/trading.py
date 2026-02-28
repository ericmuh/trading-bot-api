from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class TradingConfigUpsertRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    assets: list[str] = Field(..., min_length=1)
    timeframe: Literal["M1", "M5"]
    max_trades_per_session: int = Field(..., ge=1, le=500)
    quantity: float = Field(default=1.0, gt=0)
    profit_threshold: float = Field(default=0.02, gt=0)
    loss_threshold: float = Field(default=-0.02, lt=0)

    @field_validator("assets")
    @classmethod
    def normalize_assets(cls, value: list[str]) -> list[str]:
        normalized = [asset.strip().upper() for asset in value if asset.strip()]
        if not normalized:
            raise ValueError("assets must include at least one symbol")
        return normalized


class TradingConfigResponse(BaseModel):
    user_id: str
    assets: list[str]
    timeframe: str
    max_trades_per_session: int
    quantity: float
    profit_threshold: float
    loss_threshold: float
    updated_at: str


class TickRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    symbol: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    news_spike: bool = False
    confidence_threshold: float = Field(default=0.55, ge=0.0, le=1.0)
    timestamp: datetime | None = None

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()


class TickResponse(BaseModel):
    action: Literal["held", "opened", "closed", "rejected"]
    message: str
    symbol: str
    ai_approved: bool
    ai_confidence: float
    ai_reasons: list[str]
    side: Literal["BUY", "SELL"] | None = None
    pnl: float | None = None
    entry_price: float | None = None
    close_price: float | None = None


class AIEvaluateRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    symbol: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    news_spike: bool = False
    confidence_threshold: float = Field(default=0.55, ge=0.0, le=1.0)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()


class AIEvaluateResponse(BaseModel):
    approved: bool
    confidence: float
    reasons: list[str]
    trend_strength: float
    volatility: float


class BotStatusResponse(BaseModel):
    user_id: str
    running: bool
    started_at: str | None = None
    trades_opened_this_session: int = 0
    stop_reason: str | None = None
