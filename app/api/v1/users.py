from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.middleware.auth import get_current_user
from app.core.database import get_db
from app.domain.user.models import User
from app.domain.user.repository import UserRepository
from app.domain.user.schemas import PasswordChange, UserUpdate
from app.services.user_service import UserService

router = APIRouter()


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))


@router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    profile = await service.get_profile(current_user)
    return {
        "success": True,
        "data": profile,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.put("/me")
async def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    profile = await service.update_profile(current_user, payload.model_dump(exclude_none=True))
    return {
        "success": True,
        "data": profile,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/me/change-password")
async def change_password(
    payload: PasswordChange,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    await service.change_password(current_user, payload.current_password, payload.new_password)
    return {
        "success": True,
        "data": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
