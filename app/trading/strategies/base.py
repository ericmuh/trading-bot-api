from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

import pandas as pd


class Action(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class TradeDecision:
    action: Action
    lot_size: float
    stop_loss_pips: float
    take_profit_pips: float
    comment: str = ""
    confidence: float = 0.0


class BaseStrategy(ABC):
    name: str = ""
    version: str = "1.0"

    def __init__(self, params: dict):
        self.params = params
        self.validate_params(params)

    def validate_params(self, params: dict):
        return None

    @abstractmethod
    async def evaluate(self, tick: dict, ohlcv: pd.DataFrame, signal) -> TradeDecision:
        ...

    def default_params(self) -> dict:
        return {}
