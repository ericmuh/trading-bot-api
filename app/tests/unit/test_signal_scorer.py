from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from app.ai.signal_scorer import Direction, SignalScorer


def _sample_ohlcv(rows: int = 240) -> pd.DataFrame:
    close = np.linspace(1.0, 1.2, rows)
    open_ = close - 0.001
    high = close + 0.002
    low = close - 0.002
    volume = np.full(rows, 100)
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": volume})


@pytest.fixture
def model_files(tmp_path, monkeypatch):
    model_dir = tmp_path / "app" / "ai" / "models"
    model_dir.mkdir(parents=True, exist_ok=True)

    x_data = np.random.rand(200, 19)
    y_data = np.random.choice([0, 1, 2], size=200)
    scaler = StandardScaler().fit(x_data)
    model = RandomForestClassifier(n_estimators=20, random_state=1)
    model.fit(scaler.transform(x_data), y_data)

    joblib.dump(model, model_dir / "EURUSD_model.pkl")
    joblib.dump(scaler, model_dir / "EURUSD_scaler.pkl")
    monkeypatch.chdir(tmp_path)


def test_score_returns_signal(model_files):
    scorer = SignalScorer()
    signal = scorer.score(_sample_ohlcv(), "EURUSD")
    assert signal.direction in {Direction.BUY, Direction.SELL, Direction.HOLD}
    assert 0.0 <= signal.confidence <= 1.0
