from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.db import store


@dataclass
class TickDecision:
    action: str
    message: str
    symbol: str
    side: str | None = None
    pnl: float | None = None
    entry_price: float | None = None
    close_price: float | None = None


class TradingEngine:
    def __init__(self) -> None:
        self._last_prices: dict[tuple[str, str], float] = {}

    def process_tick(
        self,
        *,
        user_id: str,
        symbol: str,
        price: float,
        ai_approved: bool,
    ) -> TickDecision:
        config = store.get_trading_config(user_id)
        if config is None:
            return TickDecision(
                action="rejected",
                message="Trading config not found",
                symbol=symbol,
            )

        session = store.get_bot_session(user_id)
        if session is None or not bool(session["is_running"]):
            return TickDecision(
                action="held",
                message="Bot is not running",
                symbol=symbol,
            )

        session_config = store.get_session_config(user_id)
        if session_config is not None and session["started_at"]:
            started_at = datetime.fromisoformat(session["started_at"])
            now = datetime.now(timezone.utc)
            max_duration = timedelta(minutes=int(session_config["duration_minutes"]))
            if now - started_at >= max_duration:
                store.set_bot_session(
                    user_id=user_id,
                    is_running=False,
                    started_at=session["started_at"],
                    trades_opened_this_session=int(session["trades_opened_this_session"]),
                )
                return TickDecision(
                    action="held",
                    message="Bot stopped: session duration expired",
                    symbol=symbol,
                )

        risk_config = store.get_risk_config(user_id)
        if risk_config is not None:
            realized_pnl = store.get_realized_pnl_today(user_id)
            if realized_pnl >= float(risk_config["daily_profit_target"]):
                store.set_bot_session(
                    user_id=user_id,
                    is_running=False,
                    started_at=session["started_at"],
                    trades_opened_this_session=int(session["trades_opened_this_session"]),
                )
                return TickDecision(
                    action="held",
                    message="Bot stopped: daily profit target reached",
                    symbol=symbol,
                )

            if realized_pnl <= -float(risk_config["daily_loss_limit"]):
                store.set_bot_session(
                    user_id=user_id,
                    is_running=False,
                    started_at=session["started_at"],
                    trades_opened_this_session=int(session["trades_opened_this_session"]),
                )
                return TickDecision(
                    action="held",
                    message="Bot stopped: daily loss limit reached",
                    symbol=symbol,
                )

        allowed_assets = {item.strip().upper() for item in config["assets"].split(",") if item.strip()}
        if symbol not in allowed_assets:
            return TickDecision(
                action="rejected",
                message="Symbol not enabled in config",
                symbol=symbol,
            )

        open_trade = store.get_open_trade(user_id=user_id, symbol=symbol)
        if open_trade is not None:
            pnl = self._calculate_pnl(
                side=open_trade["side"],
                entry_price=float(open_trade["entry_price"]),
                current_price=price,
                quantity=float(open_trade["quantity"]),
            )

            if pnl >= float(config["profit_threshold"]):
                store.close_trade(
                    trade_id=int(open_trade["id"]),
                    close_price=price,
                    pnl=pnl,
                    reason="tp_hit",
                )
                self._last_prices[(user_id, symbol)] = price
                return TickDecision(
                    action="closed",
                    message="Trade closed on profit threshold",
                    symbol=symbol,
                    side=open_trade["side"],
                    pnl=round(pnl, 6),
                    entry_price=float(open_trade["entry_price"]),
                    close_price=price,
                )

            if pnl <= float(config["loss_threshold"]):
                store.close_trade(
                    trade_id=int(open_trade["id"]),
                    close_price=price,
                    pnl=pnl,
                    reason="sl_hit",
                )
                self._last_prices[(user_id, symbol)] = price
                return TickDecision(
                    action="closed",
                    message="Trade closed on loss threshold",
                    symbol=symbol,
                    side=open_trade["side"],
                    pnl=round(pnl, 6),
                    entry_price=float(open_trade["entry_price"]),
                    close_price=price,
                )

            self._last_prices[(user_id, symbol)] = price
            return TickDecision(
                action="held",
                message="Open trade maintained",
                symbol=symbol,
                side=open_trade["side"],
                pnl=round(pnl, 6),
                entry_price=float(open_trade["entry_price"]),
                close_price=price,
            )

        trades_opened = int(session["trades_opened_this_session"])
        max_trades = int(config["max_trades_per_session"])
        if trades_opened >= max_trades:
            self._last_prices[(user_id, symbol)] = price
            return TickDecision(
                action="held",
                message="Max trades per session reached",
                symbol=symbol,
            )

        last_price = self._last_prices.get((user_id, symbol))
        self._last_prices[(user_id, symbol)] = price

        if last_price is None:
            return TickDecision(
                action="held",
                message="Insufficient trend history",
                symbol=symbol,
            )

        if not ai_approved:
            return TickDecision(
                action="rejected",
                message="Trade rejected by AI gate",
                symbol=symbol,
            )

        if price == last_price:
            return TickDecision(
                action="held",
                message="No trend change",
                symbol=symbol,
            )

        if risk_config is not None:
            current_exposure = store.get_open_exposure(user_id)
            new_exposure = price * float(config["quantity"])
            if current_exposure + new_exposure > float(risk_config["allocated_capital"]):
                return TickDecision(
                    action="rejected",
                    message="Allocated capital limit exceeded",
                    symbol=symbol,
                )

        side = "BUY" if price > last_price else "SELL"
        store.open_trade(
            user_id=user_id,
            symbol=symbol,
            side=side,
            quantity=float(config["quantity"]),
            entry_price=price,
        )
        store.increment_session_trades(user_id)
        return TickDecision(
            action="opened",
            message="Trade opened from trend direction",
            symbol=symbol,
            side=side,
            entry_price=price,
        )

    @staticmethod
    def _calculate_pnl(*, side: str, entry_price: float, current_price: float, quantity: float) -> float:
        if side == "BUY":
            return (current_price - entry_price) * quantity
        return (entry_price - current_price) * quantity
