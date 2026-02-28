from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from app.config import get_settings


def _connect() -> sqlite3.Connection:
    settings = get_settings()
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS mt5_accounts (
                user_id TEXT PRIMARY KEY,
                login_enc TEXT NOT NULL,
                password_enc TEXT NOT NULL,
                server_enc TEXT NOT NULL,
                broker_enc TEXT,
                last_validation_status TEXT,
                last_validated_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS trading_configs (
                user_id TEXT PRIMARY KEY,
                assets TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                max_trades_per_session INTEGER NOT NULL,
                quantity REAL NOT NULL,
                profit_threshold REAL NOT NULL,
                loss_threshold REAL NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bot_sessions (
                user_id TEXT PRIMARY KEY,
                is_running INTEGER NOT NULL,
                started_at TEXT,
                trades_opened_this_session INTEGER NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS open_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity REAL NOT NULL,
                entry_price REAL NOT NULL,
                opened_at TEXT NOT NULL,
                UNIQUE(user_id, symbol)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS closed_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity REAL NOT NULL,
                entry_price REAL NOT NULL,
                close_price REAL NOT NULL,
                pnl REAL NOT NULL,
                close_reason TEXT NOT NULL,
                opened_at TEXT NOT NULL,
                closed_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                price REAL NOT NULL,
                approved INTEGER NOT NULL,
                confidence REAL NOT NULL,
                reasons TEXT NOT NULL,
                trend_strength REAL NOT NULL,
                volatility REAL NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS risk_configs (
                user_id TEXT PRIMARY KEY,
                daily_profit_target REAL NOT NULL,
                daily_loss_limit REAL NOT NULL,
                allocated_capital REAL NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS session_configs (
                user_id TEXT PRIMARY KEY,
                duration_minutes INTEGER NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                channel TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS licenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                license_key TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL,
                assigned_user_id TEXT,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS license_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                license_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                actor TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(license_id) REFERENCES licenses(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS idempotency_records (
                idempotency_key TEXT PRIMARY KEY,
                endpoint TEXT NOT NULL,
                response_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def upsert_mt5_account(
    *,
    user_id: str,
    login_enc: str,
    password_enc: str,
    server_enc: str,
    broker_enc: str | None,
    last_validation_status: str,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO mt5_accounts (
                user_id, login_enc, password_enc, server_enc, broker_enc,
                last_validation_status, last_validated_at, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                login_enc = excluded.login_enc,
                password_enc = excluded.password_enc,
                server_enc = excluded.server_enc,
                broker_enc = excluded.broker_enc,
                last_validation_status = excluded.last_validation_status,
                last_validated_at = excluded.last_validated_at,
                updated_at = excluded.updated_at
            """,
            (
                user_id,
                login_enc,
                password_enc,
                server_enc,
                broker_enc,
                last_validation_status,
                now,
                now,
                now,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_mt5_account(user_id: str) -> dict | None:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM mt5_accounts WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if row is None:
            return None
        return dict(row)
    finally:
        conn.close()


def upsert_trading_config(
    *,
    user_id: str,
    assets: list[str],
    timeframe: str,
    max_trades_per_session: int,
    quantity: float,
    profit_threshold: float,
    loss_threshold: float,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO trading_configs (
                user_id, assets, timeframe, max_trades_per_session,
                quantity, profit_threshold, loss_threshold, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                assets = excluded.assets,
                timeframe = excluded.timeframe,
                max_trades_per_session = excluded.max_trades_per_session,
                quantity = excluded.quantity,
                profit_threshold = excluded.profit_threshold,
                loss_threshold = excluded.loss_threshold,
                updated_at = excluded.updated_at
            """,
            (
                user_id,
                ",".join(assets),
                timeframe,
                max_trades_per_session,
                quantity,
                profit_threshold,
                loss_threshold,
                now,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_trading_config(user_id: str) -> dict | None:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM trading_configs WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if row is None:
            return None
        return dict(row)
    finally:
        conn.close()


def set_bot_session(
    *,
    user_id: str,
    is_running: bool,
    started_at: str | None,
    trades_opened_this_session: int,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO bot_sessions (
                user_id, is_running, started_at, trades_opened_this_session, updated_at
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                is_running = excluded.is_running,
                started_at = excluded.started_at,
                trades_opened_this_session = excluded.trades_opened_this_session,
                updated_at = excluded.updated_at
            """,
            (
                user_id,
                1 if is_running else 0,
                started_at,
                trades_opened_this_session,
                now,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_bot_session(user_id: str) -> dict | None:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM bot_sessions WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if row is None:
            return None
        return dict(row)
    finally:
        conn.close()


def increment_session_trades(user_id: str) -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            UPDATE bot_sessions
            SET trades_opened_this_session = trades_opened_this_session + 1,
                updated_at = ?
            WHERE user_id = ?
            """,
            (datetime.now(timezone.utc).isoformat(), user_id),
        )
        conn.commit()
    finally:
        conn.close()


def get_open_trade(*, user_id: str, symbol: str) -> dict | None:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM open_trades WHERE user_id = ? AND symbol = ?",
            (user_id, symbol),
        ).fetchone()
        if row is None:
            return None
        return dict(row)
    finally:
        conn.close()


def open_trade(
    *,
    user_id: str,
    symbol: str,
    side: str,
    quantity: float,
    entry_price: float,
) -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO open_trades (
                user_id, symbol, side, quantity, entry_price, opened_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, symbol) DO NOTHING
            """,
            (
                user_id,
                symbol,
                side,
                quantity,
                entry_price,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def close_trade(*, trade_id: int, close_price: float, pnl: float, reason: str) -> None:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM open_trades WHERE id = ?",
            (trade_id,),
        ).fetchone()
        if row is None:
            return

        trade = dict(row)
        conn.execute(
            """
            INSERT INTO closed_trades (
                user_id, symbol, side, quantity, entry_price,
                close_price, pnl, close_reason, opened_at, closed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trade["user_id"],
                trade["symbol"],
                trade["side"],
                trade["quantity"],
                trade["entry_price"],
                close_price,
                pnl,
                reason,
                trade["opened_at"],
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.execute("DELETE FROM open_trades WHERE id = ?", (trade_id,))
        conn.commit()
    finally:
        conn.close()


def create_ai_decision(
    *,
    user_id: str,
    symbol: str,
    price: float,
    approved: bool,
    confidence: float,
    reasons: list[str],
    trend_strength: float,
    volatility: float,
) -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO ai_decisions (
                user_id, symbol, price, approved, confidence,
                reasons, trend_strength, volatility, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                symbol,
                price,
                1 if approved else 0,
                confidence,
                ",".join(reasons),
                trend_strength,
                volatility,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def upsert_risk_config(
    *,
    user_id: str,
    daily_profit_target: float,
    daily_loss_limit: float,
    allocated_capital: float,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO risk_configs (
                user_id, daily_profit_target, daily_loss_limit, allocated_capital, updated_at
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                daily_profit_target = excluded.daily_profit_target,
                daily_loss_limit = excluded.daily_loss_limit,
                allocated_capital = excluded.allocated_capital,
                updated_at = excluded.updated_at
            """,
            (user_id, daily_profit_target, daily_loss_limit, allocated_capital, now),
        )
        conn.commit()
    finally:
        conn.close()


def get_risk_config(user_id: str) -> dict | None:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM risk_configs WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if row is None:
            return None
        return dict(row)
    finally:
        conn.close()


def upsert_session_config(*, user_id: str, duration_minutes: int) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO session_configs (user_id, duration_minutes, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                duration_minutes = excluded.duration_minutes,
                updated_at = excluded.updated_at
            """,
            (user_id, duration_minutes, now),
        )
        conn.commit()
    finally:
        conn.close()


def get_session_config(user_id: str) -> dict | None:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM session_configs WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if row is None:
            return None
        return dict(row)
    finally:
        conn.close()


def get_realized_pnl_today(user_id: str) -> float:
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()

    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(pnl), 0.0) AS realized_pnl
            FROM closed_trades
            WHERE user_id = ?
              AND closed_at >= ?
              AND closed_at <= ?
            """,
            (user_id, start_of_day, end_of_day),
        ).fetchone()
        if row is None:
            return 0.0
        return float(row["realized_pnl"])
    finally:
        conn.close()


def get_open_exposure(user_id: str) -> float:
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(entry_price * quantity), 0.0) AS exposure
            FROM open_trades
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()
        if row is None:
            return 0.0
        return float(row["exposure"])
    finally:
        conn.close()


def get_open_trades(user_id: str) -> list[dict]:
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT id, user_id, symbol, side, quantity, entry_price, opened_at
            FROM open_trades
            WHERE user_id = ?
            ORDER BY opened_at DESC
            """,
            (user_id,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_closed_trades(user_id: str, limit: int = 100) -> list[dict]:
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT id, user_id, symbol, side, quantity, entry_price,
                   close_price, pnl, close_reason, opened_at, closed_at
            FROM closed_trades
            WHERE user_id = ?
            ORDER BY closed_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_unrealized_pnl(user_id: str, current_prices: dict[str, float]) -> float:
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT symbol, side, quantity, entry_price
            FROM open_trades
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchall()
        total = 0.0
        for row in rows:
            trade = dict(row)
            symbol = trade["symbol"]
            if symbol not in current_prices:
                continue
            current = float(current_prices[symbol])
            quantity = float(trade["quantity"])
            entry = float(trade["entry_price"])
            if trade["side"] == "BUY":
                total += (current - entry) * quantity
            else:
                total += (entry - current) * quantity
        return total
    finally:
        conn.close()


def create_notification(
    *,
    user_id: str,
    event_type: str,
    title: str,
    message: str,
    channel: str,
) -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO notifications (user_id, event_type, title, message, channel, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                event_type,
                title,
                message,
                channel,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def list_notifications(user_id: str, channel: str = "in_app", limit: int = 100) -> list[dict]:
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT id, user_id, event_type, title, message, channel, created_at
            FROM notifications
            WHERE user_id = ? AND channel = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, channel, limit),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def create_license(*, license_key: str, expires_at: str, status: str = "active") -> dict:
    now = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        cursor = conn.execute(
            """
            INSERT INTO licenses (
                license_key, status, assigned_user_id, expires_at, created_at, updated_at
            )
            VALUES (?, ?, NULL, ?, ?, ?)
            """,
            (license_key, status, expires_at, now, now),
        )
        license_id = int(cursor.lastrowid)
        conn.commit()
    finally:
        conn.close()

    row = get_license_by_id(license_id)
    if row is None:
        raise ValueError("Failed to create license")
    create_license_event(
        license_id=license_id,
        event_type="created",
        actor="admin",
        metadata=f"status={status}",
    )
    return row


def get_license_by_key(license_key: str) -> dict | None:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM licenses WHERE license_key = ?",
            (license_key,),
        ).fetchone()
        if row is None:
            return None
        return dict(row)
    finally:
        conn.close()


def get_license_by_id(license_id: int) -> dict | None:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM licenses WHERE id = ?",
            (license_id,),
        ).fetchone()
        if row is None:
            return None
        return dict(row)
    finally:
        conn.close()


def get_license_by_user(user_id: str) -> dict | None:
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT *
            FROM licenses
            WHERE assigned_user_id = ?
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
        if row is None:
            return None
        return dict(row)
    finally:
        conn.close()


def activate_license_for_user(*, license_key: str, user_id: str) -> dict | None:
    row = get_license_by_key(license_key)
    if row is None:
        return None

    if row["assigned_user_id"] not in (None, user_id):
        return row

    now = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        conn.execute(
            """
            UPDATE licenses
            SET assigned_user_id = ?, updated_at = ?
            WHERE license_key = ?
            """,
            (user_id, now, license_key),
        )
        conn.commit()
    finally:
        conn.close()

    updated = get_license_by_key(license_key)
    if updated is None:
        return None
    create_license_event(
        license_id=int(updated["id"]),
        event_type="activated",
        actor=user_id,
        metadata=f"license_key={license_key}",
    )
    return updated


def update_license(
    *,
    license_id: int,
    status: str | None = None,
    expires_at: str | None = None,
) -> dict | None:
    row = get_license_by_id(license_id)
    if row is None:
        return None

    new_status = status or row["status"]
    new_expires_at = expires_at or row["expires_at"]
    now = datetime.now(timezone.utc).isoformat()

    conn = _connect()
    try:
        conn.execute(
            """
            UPDATE licenses
            SET status = ?, expires_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (new_status, new_expires_at, now, license_id),
        )
        conn.commit()
    finally:
        conn.close()

    updated = get_license_by_id(license_id)
    if updated is not None:
        create_license_event(
            license_id=license_id,
            event_type="updated",
            actor="admin",
            metadata=f"status={new_status}",
        )
    return updated


def revoke_license(license_id: int) -> dict | None:
    updated = update_license(license_id=license_id, status="revoked")
    if updated is not None:
        create_license_event(
            license_id=license_id,
            event_type="revoked",
            actor="admin",
            metadata=None,
        )
    return updated


def list_licenses(limit: int = 200) -> list[dict]:
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT *
            FROM licenses
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def create_license_event(*, license_id: int, event_type: str, actor: str, metadata: str | None) -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO license_events (license_id, event_type, actor, metadata, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                license_id,
                event_type,
                actor,
                metadata,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def is_license_valid_for_user(user_id: str) -> tuple[bool, str]:
    license_row = get_license_by_user(user_id)
    if license_row is None:
        return False, "No license is activated"

    status = str(license_row["status"])
    if status == "revoked":
        return False, "License is revoked"
    if status == "expired":
        return False, "License is expired"

    now = datetime.now(timezone.utc)
    expires_at = datetime.fromisoformat(str(license_row["expires_at"]))
    if expires_at < now:
        update_license(license_id=int(license_row["id"]), status="expired")
        return False, "License is expired"

    return True, "License is valid"


def get_idempotent_response(*, idempotency_key: str, endpoint: str) -> dict | None:
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT response_json
            FROM idempotency_records
            WHERE idempotency_key = ? AND endpoint = ?
            """,
            (idempotency_key, endpoint),
        ).fetchone()
        if row is None:
            return None
        return json.loads(str(row["response_json"]))
    finally:
        conn.close()


def save_idempotent_response(*, idempotency_key: str, endpoint: str, response: dict) -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO idempotency_records (
                idempotency_key, endpoint, response_json, created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                idempotency_key,
                endpoint,
                json.dumps(response),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def stop_all_running_bots() -> int:
    now = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        cursor = conn.execute(
            """
            UPDATE bot_sessions
            SET is_running = 0,
                updated_at = ?
            WHERE is_running = 1
            """,
            (now,),
        )
        conn.commit()
        return int(cursor.rowcount)
    finally:
        conn.close()
