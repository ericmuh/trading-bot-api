import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.sqltypes import BINARY_TYPE, GUID


class MT5Account(Base):
    __tablename__ = "mt5_accounts"
    __table_args__ = (UniqueConstraint("user_id", "login", "server", name="uq_user_login_server"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("users.id", ondelete="CASCADE"))
    broker_name: Mapped[str] = mapped_column(String(100), nullable=False)
    server: Mapped[str] = mapped_column(String(100), nullable=False)
    login: Mapped[int] = mapped_column(BigInteger, nullable=False)
    password_enc: Mapped[bytes] = mapped_column(BINARY_TYPE, nullable=False)
    account_type: Mapped[str | None] = mapped_column(String(20))
    currency: Mapped[str | None] = mapped_column(String(10))
    leverage: Mapped[int | None] = mapped_column(Integer)
    balance: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
