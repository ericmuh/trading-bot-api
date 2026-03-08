from dataclasses import dataclass
from enum import Enum

import pandas as pd


class TrendDirection(str, Enum):
    BULL = "BULL"
    BEAR = "BEAR"
    RANGING = "RANGING"


@dataclass
class TrendResult:
    direction: TrendDirection
    strength: float


class TrendDetector:
    def detect(self, ohlcv: pd.DataFrame) -> TrendResult:
        ema_20 = ohlcv["close"].ewm(span=20).mean().iloc[-1]
        ema_50 = ohlcv["close"].ewm(span=50).mean().iloc[-1]
        ema_200 = ohlcv["close"].ewm(span=200).mean().iloc[-1]
        adx = ohlcv.get("adx", pd.Series([25])).iloc[-1]

        if adx < 20:
            return TrendResult(TrendDirection.RANGING, float(adx))
        if ema_20 > ema_50 > ema_200:
            return TrendResult(TrendDirection.BULL, float(adx))
        if ema_20 < ema_50 < ema_200:
            return TrendResult(TrendDirection.BEAR, float(adx))
        return TrendResult(TrendDirection.RANGING, float(adx))

