from app.trading.strategies.base import BaseStrategy
from app.trading.strategies.base import Action, TradeDecision


class TrendFollowStrategy(BaseStrategy):
    name = "TrendFollowStrategy"

    async def evaluate(self, tick: dict, ohlcv, signal) -> TradeDecision:
        if signal.direction.value == "BUY":
            return TradeDecision(Action.BUY, 0.02, signal.sl_pips, signal.tp_pips, "trend-buy", signal.confidence)
        if signal.direction.value == "SELL":
            return TradeDecision(
                Action.SELL,
                0.02,
                signal.sl_pips,
                signal.tp_pips,
                "trend-sell",
                signal.confidence,
            )
        return TradeDecision(Action.HOLD, 0.01, 0, 0, "trend-hold", signal.confidence)
