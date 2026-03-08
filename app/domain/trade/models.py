import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.sqltypes import GUID


class Trade(Base):
    __tablename__ = "trades"
    __table_args__ = (
        Index("idx_trades_bot_id", "bot_id"),
        Index("idx_trades_status", "status"),
        Index("idx_trades_open_time", "open_time"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    bot_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("bots.id"))
    account_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("mt5_accounts.id"))
    mt5_ticket: Mapped[int | None] = mapped_column(BigInteger, unique=True)
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
    ai_signal_id: Mapped[uuid.UUID | None] = mapped_column(GUID)
    idempotency_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
