from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.middleware.auth import get_current_user
from app.core.database import get_db
from app.domain.bot.repository import BotRepository
from app.domain.bot.schemas import BotCreate, BotResponse, BotUpdate
from app.services.bot_service import BotService

router = APIRouter()


def get_bot_service(db: AsyncSession = Depends(get_db)) -> BotService:
    return BotService(BotRepository(db))


@router.get("")
async def list_bots(
    current_user=Depends(get_current_user),
    service: BotService = Depends(get_bot_service),
):
    bots = await service.list_bots(current_user.id)
    return {
        "success": True,
        "data": [BotResponse.model_validate(item) for item in bots],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("", status_code=201)
async def create_bot(
    payload: BotCreate,
    current_user=Depends(get_current_user),
    service: BotService = Depends(get_bot_service),
):
    bot = await service.create_bot(current_user.id, payload)
    return {
        "success": True,
        "data": BotResponse.model_validate(bot),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/{bot_id}")
async def get_bot(
    bot_id: UUID,
    current_user=Depends(get_current_user),
    service: BotService = Depends(get_bot_service),
):
    bot = await service.get_bot(current_user.id, bot_id)
    return {
        "success": True,
        "data": BotResponse.model_validate(bot),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.put("/{bot_id}")
async def update_bot(
    bot_id: UUID,
    payload: BotUpdate,
    current_user=Depends(get_current_user),
    service: BotService = Depends(get_bot_service),
):
    bot = await service.update_bot(current_user.id, bot_id, payload.model_dump(exclude_none=True))
    return {
        "success": True,
        "data": BotResponse.model_validate(bot),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.delete("/{bot_id}", status_code=204)
async def delete_bot(
    bot_id: UUID,
    current_user=Depends(get_current_user),
    service: BotService = Depends(get_bot_service),
):
    await service.delete_bot(current_user.id, bot_id)


@router.post("/{bot_id}/start")
async def start_bot(
    bot_id: UUID,
    current_user=Depends(get_current_user),
    service: BotService = Depends(get_bot_service),
):
    await service.start_bot(current_user.id, bot_id)
    return {
        "success": True,
        "data": {"state": "starting"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/{bot_id}/stop")
async def stop_bot(
    bot_id: UUID,
    current_user=Depends(get_current_user),
    service: BotService = Depends(get_bot_service),
):
    await service.stop_bot(current_user.id, bot_id)
    return {
        "success": True,
        "data": {"state": "stopping"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/{bot_id}/pause")
async def pause_bot(
    bot_id: UUID,
    current_user=Depends(get_current_user),
    service: BotService = Depends(get_bot_service),
):
    await service.pause_bot(current_user.id, bot_id)
    return {
        "success": True,
        "data": {"state": "paused"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
