from __future__ import annotations

from app.db import store


class DashboardService:
    def current_prices(self, user_id: str) -> dict[str, float]:
        prices: dict[str, float] = {}
        for trade in store.get_open_trades(user_id):
            prices[str(trade["symbol"])] = float(trade["entry_price"])
        return prices

    def summary(self, user_id: str) -> dict:
        risk_config = store.get_risk_config(user_id)
        allocated_capital = float(risk_config["allocated_capital"]) if risk_config else 0.0

        realized = store.get_realized_pnl_today(user_id)
        unrealized = store.get_unrealized_pnl(user_id, self.current_prices(user_id))
        margin = store.get_open_exposure(user_id)

        session = store.get_bot_session(user_id)
        running = bool(session["is_running"]) if session else False

        balance = allocated_capital + realized
        equity = balance + unrealized

        return {
            "user_id": user_id,
            "balance": round(balance, 6),
            "equity": round(equity, 6),
            "margin": round(margin, 6),
            "daily_realized_pnl": round(realized, 6),
            "daily_unrealized_pnl": round(unrealized, 6),
            "bot_running": running,
        }
