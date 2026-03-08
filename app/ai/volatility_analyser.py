from dataclasses import dataclass
from enum import Enum

import pandas as pd


class VolatilityRegime(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"


@dataclass
class VolatilityResult:
    regime: VolatilityRegime
    atr: float
    sl_multiplier: float
    tp_multiplier: float


class VolatilityAnalyser:
    def analyse(self, ohlcv: pd.DataFrame) -> VolatilityResult:
        atr = ohlcv["close"].diff().abs().rolling(14).mean().iloc[-1]
        atr_ma = ohlcv["close"].diff().abs().rolling(50).mean().iloc[-1]
        ratio = atr / atr_ma if atr_ma and atr_ma > 0 else 1.0

        if ratio < 0.7:
            regime = VolatilityRegime.LOW
            sl_mult, tp_mult = 1.0, 1.5
        elif ratio > 1.5:
            regime = VolatilityRegime.HIGH
            sl_mult, tp_mult = 2.0, 3.0
        else:
            regime = VolatilityRegime.NORMAL
            sl_mult, tp_mult = 1.5, 2.5

        return VolatilityResult(regime=regime, atr=float(atr), sl_multiplier=sl_mult, tp_multiplier=tp_mult)

