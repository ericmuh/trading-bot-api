from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TradeResponse(BaseModel):
    id: UUID
    bot_id: UUID
    account_id: UUID
    symbol: str
    direction: str
    lot_size: float
    open_price: float | None
    close_price: float | None
    profit: float | None
    status: str
    open_time: datetime
    close_time: datetime | None

    model_config = {"from_attributes": True}
