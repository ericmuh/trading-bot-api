import numpy as np
import pandas as pd

from app.ai.trend_detector import TrendDetector
from app.ai.volatility_analyser import VolatilityAnalyser


def _sample_df(rows: int = 240):
    close = np.linspace(1.0, 1.3, rows)
    open_ = close - 0.001
    high = close + 0.002
    low = close - 0.002
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close})


def test_trend_detector_returns_direction():
    detector = TrendDetector()
    result = detector.detect(_sample_df())
    assert result.direction.value in {"BULL", "BEAR", "RANGING"}


def test_volatility_analyser_returns_regime():
    analyser = VolatilityAnalyser()
    result = analyser.analyse(_sample_df())
    assert result.regime.value in {"LOW", "NORMAL", "HIGH"}
