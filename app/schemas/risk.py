from __future__ import annotations

from pydantic import BaseModel, Field


class RiskConfigUpsertRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    daily_profit_target: float = Field(..., gt=0)
    daily_loss_limit: float = Field(..., gt=0)
    allocated_capital: float = Field(..., gt=0)


class RiskConfigResponse(BaseModel):
    user_id: str
    daily_profit_target: float
    daily_loss_limit: float
    allocated_capital: float
    updated_at: str


class SessionConfigUpsertRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    duration_minutes: int = Field(..., ge=1, le=1440)


class SessionConfigResponse(BaseModel):
    user_id: str
    duration_minutes: int
    updated_at: str
