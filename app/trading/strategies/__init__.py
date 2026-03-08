from app.trading.strategies.base import BaseStrategy
from app.trading.strategies.mean_reversion import MeanReversionStrategy
from app.trading.strategies.scalping import ScalpingStrategy
from app.trading.strategies.trend_follow import TrendFollowStrategy

STRATEGY_REGISTRY: dict[str, type[BaseStrategy]] = {
	"ScalpingStrategy": ScalpingStrategy,
	"TrendFollowStrategy": TrendFollowStrategy,
	"MeanReversionStrategy": MeanReversionStrategy,
}


def get_strategy(class_name: str, params: dict) -> BaseStrategy:
	cls = STRATEGY_REGISTRY.get(class_name)
	if not cls:
		raise ValueError(f"Unknown strategy: {class_name}")
	return cls(params)

