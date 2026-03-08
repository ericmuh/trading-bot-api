from app.core.exceptions import AppException
from app.core.redis import get_redis
from app.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.domain.user.repository import UserRepository


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register(self, email: str, password: str, full_name: str):
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise AppException("EMAIL_TAKEN", "Email already registered", 409)
        hashed = hash_password(password)
        return await self.user_repo.create(email=email, password_hash=hashed, full_name=full_name)

    async def login(self, email: str, password: str) -> dict:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise AppException("INVALID_CREDENTIALS", "Email or password incorrect", 401)
        if not user.is_active:
            raise AppException("ACCOUNT_DISABLED", "Account is disabled", 403)
        access_token = create_access_token(str(user.id))
        refresh_token, jti = create_refresh_token(str(user.id))
        try:
            redis = await get_redis()
            await redis.setex(f"refresh:valid:{jti}", 60 * 60 * 24 * 30, str(user.id))
        except RuntimeError:
            if settings.REDIS_REQUIRED:
                raise AppException("REDIS_UNAVAILABLE", "Authentication store unavailable", 503)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def refresh(self, refresh_token: str) -> dict:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise AppException("INVALID_TOKEN", "Not a refresh token", 401)
        jti = payload["jti"]
        try:
            redis = await get_redis()
            if not await redis.exists(f"refresh:valid:{jti}"):
                raise AppException("TOKEN_REVOKED", "Refresh token has been revoked", 401)
        except RuntimeError:
            if settings.REDIS_REQUIRED:
                raise AppException("REDIS_UNAVAILABLE", "Authentication store unavailable", 503)
        access_token = create_access_token(payload["sub"])
        return {"access_token": access_token, "token_type": "bearer"}

    async def logout(self, refresh_token: str):
        payload = decode_token(refresh_token)
        jti = payload.get("jti")
        if jti:
            try:
                redis = await get_redis()
                await redis.delete(f"refresh:valid:{jti}")
            except RuntimeError:
                if settings.REDIS_REQUIRED:
                    raise AppException("REDIS_UNAVAILABLE", "Authentication store unavailable", 503)
