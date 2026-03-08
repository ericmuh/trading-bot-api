from dataclasses import dataclass

from app.trading.strategies.base import Action, TradeDecision


@dataclass
class RiskConfig:
    lot_size: float
    max_trades: int
    max_drawdown_pct: float


class RiskBreachError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class RiskManager:
    def __init__(self, config: dict | RiskConfig):
        if isinstance(config, RiskConfig):
            self.config = config
        else:
            self.config = RiskConfig(
                lot_size=float(config.get("lot_size", 0.01)),
                max_trades=int(config.get("max_trades", 5)),
                max_drawdown_pct=float(config.get("max_drawdown_pct", 5.0)),
            )

    async def validate(
        self,
        decision: TradeDecision,
        open_trade_count: int,
        account_info: dict,
        day_start_balance: float,
    ):
        if decision.action == Action.HOLD:
            return

        if open_trade_count >= self.config.max_trades:
            raise RiskBreachError("MAX_TRADES", f"Open trades ({open_trade_count}) at limit")

        if decision.stop_loss_pips <= 0:
            raise RiskBreachError("NO_STOP_LOSS", "Stop loss is required")

        if decision.lot_size < 0.01 or decision.lot_size > self.config.lot_size * 3:
            raise RiskBreachError("INVALID_LOT_SIZE", f"Lot size {decision.lot_size} out of range")

        equity = float(account_info.get("equity", 0))
        if day_start_balance > 0:
            drawdown_pct = ((day_start_balance - equity) / day_start_balance) * 100
            if drawdown_pct >= self.config.max_drawdown_pct:
                raise RiskBreachError("MAX_DRAWDOWN", f"Drawdown {drawdown_pct:.1f}% exceeds limit")

        free_margin = float(account_info.get("free_margin", 0))
        if free_margin < 50:
            raise RiskBreachError("INSUFFICIENT_MARGIN", "Insufficient free margin")

