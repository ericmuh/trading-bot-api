import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.sqltypes import GUID


class Bot(Base):
    __tablename__ = "bots"
    __table_args__ = (
        Index("idx_bots_state", "state"),
        Index("idx_bots_user_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("users.id", ondelete="CASCADE"))
    account_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("mt5_accounts.id"))
    strategy_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("strategies.id"))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)
    state: Mapped[str] = mapped_column(String(20), default="stopped")
    lot_size: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.01"))
    max_trades: Mapped[int] = mapped_column(Integer, default=5)
    max_drawdown_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("5.0"))
    min_ai_confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), default=Decimal("0.65"))
    worker_pod_id: Mapped[str | None] = mapped_column(String(100))
    last_heartbeat: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
