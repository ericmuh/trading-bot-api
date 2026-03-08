from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.user.repository import UserRepository
from app.domain.user.schemas import TokenResponse, UserLogin, UserRegister
from app.services.auth_service import AuthService

router = APIRouter()


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db))


@router.post("/register", status_code=201)
async def register(payload: UserRegister, service: AuthService = Depends(get_auth_service)):
    user = await service.register(payload.email, payload.password, payload.full_name)
    return {
        "success": True,
        "data": {"id": str(user.id), "email": user.email},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, service: AuthService = Depends(get_auth_service)):
    tokens = await service.login(payload.email, payload.password)
    return {
        "success": True,
        "data": tokens,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/refresh")
async def refresh(payload: dict, service: AuthService = Depends(get_auth_service)):
    tokens = await service.refresh(payload["refresh_token"])
    return {
        "success": True,
        "data": tokens,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/logout")
async def logout(payload: dict, service: AuthService = Depends(get_auth_service)):
    await service.logout(payload["refresh_token"])
    return {
        "success": True,
        "data": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
