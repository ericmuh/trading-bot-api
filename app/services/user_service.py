from app.core.exceptions import AppException
from app.core.security import hash_password, verify_password
from app.domain.user.models import User
from app.domain.user.repository import UserRepository


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def get_profile(self, user: User) -> dict:
        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "tier": user.tier,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat(),
        }

    async def update_profile(self, user: User, updates: dict) -> dict:
        allowed = {"full_name", "phone"}
        for key, value in updates.items():
            if key in allowed and value is not None:
                setattr(user, key, value)
        await self.user_repo.save(user)
        return await self.get_profile(user)

    async def change_password(self, user: User, current_password: str, new_password: str):
        if not verify_password(current_password, user.password_hash):
            raise AppException("INVALID_PASSWORD", "Current password is incorrect", 400)
        user.password_hash = hash_password(new_password)
        await self.user_repo.save(user)
