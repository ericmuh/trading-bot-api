from app.trading.strategies import get_strategy


class StrategyEngine:
    @staticmethod
    def build(class_name: str, params: dict):
        return get_strategy(class_name, params)

