import uuid

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import AppException
from app.core.security import encrypt_credential
from app.domain.mt5_account.repository import MT5AccountRepository
from app.domain.mt5_account.schemas import MT5ConnectRequest


class MT5Service:
    def __init__(self, account_repo: MT5AccountRepository):
        self.account_repo = account_repo

    async def connect_account(self, user_id: uuid.UUID, payload: MT5ConnectRequest):
        password_enc = encrypt_credential(payload.password)
        try:
            return await self.account_repo.create(
                user_id=user_id,
                broker_name=payload.broker_name,
                server=payload.server,
                login=payload.login,
                password_enc=password_enc,
                account_type=payload.account_type,
            )
        except IntegrityError as error:
            raise AppException(
                "DUPLICATE_ACCOUNT",
                "Account with this login/server already exists for user",
                409,
            ) from error

    async def list_accounts(self, user_id: uuid.UUID):
        return await self.account_repo.list_by_user(user_id)

    async def disconnect_account(self, user_id: uuid.UUID, account_id: uuid.UUID):
        account = await self.account_repo.get_by_id(account_id, user_id)
        if not account:
            raise AppException("ACCOUNT_NOT_FOUND", "MT5 account not found", 404)
        await self.account_repo.soft_delete(account)

    async def get_live_balance(self, user_id: uuid.UUID, account_id: uuid.UUID) -> dict:
        account = await self.account_repo.get_by_id(account_id, user_id)
        if not account:
            raise AppException("ACCOUNT_NOT_FOUND", "MT5 account not found", 404)

        from app.trading.session_manager import session_pool

        session = await session_pool.get(str(account_id))
        if not session or not session.is_connected:
            raise AppException("SESSION_INACTIVE", "No active MT5 session for this account", 503)

        info = await session.get_account_info()
        positions = await session.get_positions()
        return {"account_info": info, "open_positions": positions}
