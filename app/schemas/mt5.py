from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ConnectTestRequest(BaseModel):
    login: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    server: str = Field(..., min_length=1)
    timeout_ms: int = Field(default=2000, ge=200, le=10000)


class ConnectTestResponse(BaseModel):
    status: Literal["validated", "failed", "provider_unavailable"]
    provider: str
    latency_ms: int
    message: str


class MT5AccountUpsertRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    login: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    server: str = Field(..., min_length=1)
    broker: str | None = None
    timeout_ms: int = Field(default=2000, ge=200, le=10000)


class MT5AccountStatusResponse(BaseModel):
    user_id: str
    configured: bool
    login: str | None = None
    server: str | None = None
    broker: str | None = None
    last_validation_status: str | None = None
    last_validated_at: str | None = None
