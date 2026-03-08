from app.trading.strategies.base import BaseStrategy
from app.trading.strategies.base import Action, TradeDecision


class ScalpingStrategy(BaseStrategy):
    name = "ScalpingStrategy"

    async def evaluate(self, tick: dict, ohlcv, signal) -> TradeDecision:
        if signal.direction.value == "BUY":
            return TradeDecision(Action.BUY, 0.01, 8, 12, "scalp-buy", signal.confidence)
        if signal.direction.value == "SELL":
            return TradeDecision(Action.SELL, 0.01, 8, 12, "scalp-sell", signal.confidence)
        return TradeDecision(Action.HOLD, 0.01, 0, 0, "scalp-hold", signal.confidence)
