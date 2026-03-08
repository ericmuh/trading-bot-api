"""phase 1 initial schema

Revision ID: 20260308_01
Revises:
Create Date: 2026-03-08
"""

from alembic import op
import sqlalchemy as sa


revision = "20260308_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("tier", sa.String(length=20), nullable=False, server_default="free"),
        sa.Column("mfa_secret", sa.String(length=64), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "strategies",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("class_name", sa.String(length=100), nullable=False),
        sa.Column("default_params", sa.JSON(), nullable=True),
        sa.Column("param_schema", sa.JSON(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("author_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("version", sa.String(length=20), nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "mt5_accounts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("broker_name", sa.String(length=100), nullable=False),
        sa.Column("server", sa.String(length=100), nullable=False),
        sa.Column("login", sa.BigInteger(), nullable=False),
        sa.Column("password_enc", sa.LargeBinary(), nullable=False),
        sa.Column("account_type", sa.String(length=20), nullable=True),
        sa.Column("currency", sa.String(length=10), nullable=True),
        sa.Column("leverage", sa.Integer(), nullable=True),
        sa.Column("balance", sa.Numeric(18, 2), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "login", "server", name="uq_user_login_server"),
    )

    op.create_table(
        "bots",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("account_id", sa.String(length=36), sa.ForeignKey("mt5_accounts.id"), nullable=False),
        sa.Column("strategy_id", sa.String(length=36), sa.ForeignKey("strategies.id"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("timeframe", sa.String(length=10), nullable=False),
        sa.Column("state", sa.String(length=20), nullable=False, server_default="stopped"),
        sa.Column("lot_size", sa.Numeric(10, 2), nullable=False, server_default="0.01"),
        sa.Column("max_trades", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("max_drawdown_pct", sa.Numeric(5, 2), nullable=False, server_default="5.0"),
        sa.Column("min_ai_confidence", sa.Numeric(4, 3), nullable=False, server_default="0.650"),
        sa.Column("worker_pod_id", sa.String(length=100), nullable=True),
        sa.Column("last_heartbeat", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_bots_state", "bots", ["state"])
    op.create_index("idx_bots_user_id", "bots", ["user_id"])

    op.create_table(
        "trades",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("bot_id", sa.String(length=36), sa.ForeignKey("bots.id"), nullable=False),
        sa.Column("account_id", sa.String(length=36), sa.ForeignKey("mt5_accounts.id"), nullable=False),
        sa.Column("mt5_ticket", sa.BigInteger(), nullable=True, unique=True),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("direction", sa.String(length=10), nullable=False),
        sa.Column("lot_size", sa.Numeric(10, 2), nullable=False),
        sa.Column("open_price", sa.Numeric(18, 5), nullable=True),
        sa.Column("close_price", sa.Numeric(18, 5), nullable=True),
        sa.Column("stop_loss", sa.Numeric(18, 5), nullable=True),
        sa.Column("take_profit", sa.Numeric(18, 5), nullable=True),
        sa.Column("profit", sa.Numeric(18, 2), nullable=True),
        sa.Column("commission", sa.Numeric(18, 2), nullable=True),
        sa.Column("swap", sa.Numeric(18, 2), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("open_time", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("close_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ai_confidence", sa.Numeric(4, 3), nullable=True),
        sa.Column("ai_signal_id", sa.String(length=36), nullable=True),
        sa.Column("idempotency_key", sa.String(length=64), nullable=False, unique=True),
    )
    op.create_index("idx_trades_bot_id", "trades", ["bot_id"])
    op.create_index("idx_trades_status", "trades", ["status"])
    op.create_index("idx_trades_open_time", "trades", ["open_time"])


def downgrade() -> None:
    op.drop_index("idx_trades_open_time", table_name="trades")
    op.drop_index("idx_trades_status", table_name="trades")
    op.drop_index("idx_trades_bot_id", table_name="trades")
    op.drop_table("trades")

    op.drop_index("idx_bots_user_id", table_name="bots")
    op.drop_index("idx_bots_state", table_name="bots")
    op.drop_table("bots")

    op.drop_table("mt5_accounts")
    op.drop_table("strategies")
    op.drop_table("users")
