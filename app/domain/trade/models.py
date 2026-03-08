import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bots.id"))
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("mt5_accounts.id"))
    mt5_ticket: Mapped[int | None] = mapped_column(unique=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    lot_size: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    open_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 5))
    close_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 5))
    stop_loss: Mapped[Decimal | None] = mapped_column(Numeric(18, 5))
    take_profit: Mapped[Decimal | None] = mapped_column(Numeric(18, 5))
    profit: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    commission: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    swap: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    status: Mapped[str] = mapped_column(String(20), default="open")
    open_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    close_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ai_confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    ai_signal_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    idempotency_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
