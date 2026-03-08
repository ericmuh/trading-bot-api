from app.trading.strategies.base import BaseStrategy
from app.trading.strategies.base import Action, TradeDecision


class MeanReversionStrategy(BaseStrategy):
    name = "MeanReversionStrategy"

    async def evaluate(self, tick: dict, ohlcv, signal) -> TradeDecision:
        if signal.direction.value == "BUY":
            return TradeDecision(Action.BUY, 0.01, 12, 10, "mr-buy", signal.confidence)
        if signal.direction.value == "SELL":
            return TradeDecision(Action.SELL, 0.01, 12, 10, "mr-sell", signal.confidence)
        return TradeDecision(Action.HOLD, 0.01, 0, 0, "mr-hold", signal.confidence)

