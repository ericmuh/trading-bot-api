from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.db import store
from app.schemas.risk import (
    RiskConfigResponse,
    RiskConfigUpsertRequest,
    SessionConfigResponse,
    SessionConfigUpsertRequest,
)

router = APIRouter(tags=["risk"])


@router.put("/risk/config", response_model=RiskConfigResponse)
def upsert_risk_config(payload: RiskConfigUpsertRequest) -> RiskConfigResponse:
    store.upsert_risk_config(
        user_id=payload.user_id,
        daily_profit_target=payload.daily_profit_target,
        daily_loss_limit=payload.daily_loss_limit,
        allocated_capital=payload.allocated_capital,
    )
    row = store.get_risk_config(payload.user_id)
    if row is None:
        raise HTTPException(status_code=500, detail="Failed to persist risk config")

    return RiskConfigResponse(
        user_id=row["user_id"],
        daily_profit_target=float(row["daily_profit_target"]),
        daily_loss_limit=float(row["daily_loss_limit"]),
        allocated_capital=float(row["allocated_capital"]),
        updated_at=row["updated_at"],
    )


@router.get("/risk/config", response_model=RiskConfigResponse)
def get_risk_config(user_id: str) -> RiskConfigResponse:
    row = store.get_risk_config(user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Risk config not found")

    return RiskConfigResponse(
        user_id=row["user_id"],
        daily_profit_target=float(row["daily_profit_target"]),
        daily_loss_limit=float(row["daily_loss_limit"]),
        allocated_capital=float(row["allocated_capital"]),
        updated_at=row["updated_at"],
    )


@router.put("/session/config", response_model=SessionConfigResponse)
def upsert_session_config(payload: SessionConfigUpsertRequest) -> SessionConfigResponse:
    store.upsert_session_config(
        user_id=payload.user_id,
        duration_minutes=payload.duration_minutes,
    )
    row = store.get_session_config(payload.user_id)
    if row is None:
        raise HTTPException(status_code=500, detail="Failed to persist session config")

    return SessionConfigResponse(
        user_id=row["user_id"],
        duration_minutes=int(row["duration_minutes"]),
        updated_at=row["updated_at"],
    )


@router.get("/session/config", response_model=SessionConfigResponse)
def get_session_config(user_id: str) -> SessionConfigResponse:
    row = store.get_session_config(user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Session config not found")

    return SessionConfigResponse(
        user_id=row["user_id"],
        duration_minutes=int(row["duration_minutes"]),
        updated_at=row["updated_at"],
    )
