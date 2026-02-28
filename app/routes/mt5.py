from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.db.store import get_mt5_account, upsert_mt5_account
from app.schemas.mt5 import (
    ConnectTestRequest,
    ConnectTestResponse,
    MT5AccountStatusResponse,
    MT5AccountUpsertRequest,
)
from app.services.crypto import CryptoService
from app.services.mt5_connector import MT5Connector

router = APIRouter(prefix="/mt5", tags=["mt5"])
connector = MT5Connector()
crypto = CryptoService()


@router.post("/connect-test", response_model=ConnectTestResponse)
def connect_test(payload: ConnectTestRequest) -> ConnectTestResponse:
    result = connector.validate_credentials(
        login=payload.login,
        password=payload.password,
        server=payload.server,
        timeout_ms=payload.timeout_ms,
    )
    return ConnectTestResponse(
        status=result.status,
        provider=result.provider,
        latency_ms=result.latency_ms,
        message=result.message,
    )


@router.put("/account")
def upsert_account(payload: MT5AccountUpsertRequest) -> dict:
    result = connector.validate_credentials(
        login=payload.login,
        password=payload.password,
        server=payload.server,
        timeout_ms=payload.timeout_ms,
    )

    if result.status == "failed":
        raise HTTPException(status_code=400, detail=result.message)

    upsert_mt5_account(
        user_id=payload.user_id,
        login_enc=crypto.encrypt(payload.login),
        password_enc=crypto.encrypt(payload.password),
        server_enc=crypto.encrypt(payload.server),
        broker_enc=crypto.encrypt(payload.broker) if payload.broker else None,
        last_validation_status=result.status,
    )

    return {
        "saved": True,
        "validation_status": result.status,
        "validation_message": result.message,
    }


@router.get("/account/status", response_model=MT5AccountStatusResponse)
def account_status(user_id: str) -> MT5AccountStatusResponse:
    row = get_mt5_account(user_id)
    if row is None:
        return MT5AccountStatusResponse(user_id=user_id, configured=False)

    return MT5AccountStatusResponse(
        user_id=user_id,
        configured=True,
        login=crypto.decrypt(row["login_enc"]),
        server=crypto.decrypt(row["server_enc"]),
        broker=crypto.decrypt(row["broker_enc"]) if row["broker_enc"] else None,
        last_validation_status=row["last_validation_status"],
        last_validated_at=row["last_validated_at"],
    )
