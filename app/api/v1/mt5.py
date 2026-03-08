from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.middleware.auth import get_current_user
from app.core.database import get_db
from app.domain.mt5_account.repository import MT5AccountRepository
from app.domain.mt5_account.schemas import MT5AccountResponse, MT5ConnectRequest
from app.services.mt5_service import MT5Service

router = APIRouter()


def get_mt5_service(db: AsyncSession = Depends(get_db)) -> MT5Service:
    return MT5Service(MT5AccountRepository(db))


@router.post("/connect", status_code=201)
async def connect_account(
    payload: MT5ConnectRequest,
    current_user=Depends(get_current_user),
    service: MT5Service = Depends(get_mt5_service),
):
    account = await service.connect_account(current_user.id, payload)
    return {
        "success": True,
        "data": MT5AccountResponse.model_validate(account),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/accounts")
async def list_accounts(
    current_user=Depends(get_current_user),
    service: MT5Service = Depends(get_mt5_service),
):
    accounts = await service.list_accounts(current_user.id)
    return {
        "success": True,
        "data": [MT5AccountResponse.model_validate(item) for item in accounts],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.delete("/accounts/{account_id}", status_code=204)
async def disconnect_account(
    account_id: UUID,
    current_user=Depends(get_current_user),
    service: MT5Service = Depends(get_mt5_service),
):
    await service.disconnect_account(current_user.id, account_id)


@router.get("/accounts/{account_id}/balance")
async def get_live_balance(
    account_id: UUID,
    current_user=Depends(get_current_user),
    service: MT5Service = Depends(get_mt5_service),
):
    data = await service.get_live_balance(current_user.id, account_id)
    return {
        "success": True,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
