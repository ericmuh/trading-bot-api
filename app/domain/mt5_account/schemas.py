from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class MT5ConnectRequest(BaseModel):
    broker_name: str
    server: str
    login: int
    password: str
    account_type: str = "demo"


class MT5AccountResponse(BaseModel):
    id: UUID
    broker_name: str
    server: str
    login: int
    account_type: str | None
    currency: str | None
    leverage: int | None
    balance: float | None
    is_active: bool
    last_synced_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
