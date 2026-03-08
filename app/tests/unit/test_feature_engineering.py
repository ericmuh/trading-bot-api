import numpy as np
import pandas as pd
import pytest

from app.ai.feature_engineering import FeatureEngineer


def _sample_ohlcv(rows: int = 240) -> pd.DataFrame:
    close = np.linspace(1.0, 1.2, rows)
    open_ = close - 0.001
    high = close + 0.002
    low = close - 0.002
    volume = np.full(rows, 100)
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": volume})


def test_extract_feature_count():
    engineer = FeatureEngineer()
    features = engineer.extract(_sample_ohlcv())
    assert len(features.columns) == 19


def test_extract_raises_with_insufficient_rows():
    engineer = FeatureEngineer()
    with pytest.raises(ValueError):
        engineer.extract(_sample_ohlcv(100))
