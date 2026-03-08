from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

import joblib
import numpy as np

from app.ai.feature_engineering import FeatureEngineer


class Direction(str, Enum):
    HOLD = "HOLD"
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class Signal:
    direction: Direction
    confidence: float
    sl_pips: float
    tp_pips: float
    timestamp: datetime


_MODEL_CACHE: dict[str, dict] = {}


def _load_model(symbol: str):
    if symbol not in _MODEL_CACHE:
        model_dir = Path("app/ai/models")
        model_path = model_dir / f"{symbol}_model.pkl"
        scaler_path = model_dir / f"{symbol}_scaler.pkl"
        if not model_path.exists() or not scaler_path.exists():
            raise FileNotFoundError(f"Model files missing for symbol {symbol}")
        _MODEL_CACHE[symbol] = {
            "model": joblib.load(model_path),
            "scaler": joblib.load(scaler_path),
        }
    return _MODEL_CACHE[symbol]


class SignalScorer:
    def __init__(self):
        self.fe = FeatureEngineer()

    def score(self, ohlcv, symbol: str) -> Signal:
        cached = _load_model(symbol)
        features = self.fe.extract(ohlcv)
        scaled = cached["scaler"].transform(features.values)
        proba = cached["model"].predict_proba(scaled)[0]
        label_map = {0: Direction.HOLD, 1: Direction.BUY, 2: Direction.SELL}
        direction = label_map[int(np.argmax(proba))]
        confidence = float(np.max(proba))
        atr = float(features.attrs.get("atr", 10.0))
        return Signal(
            direction=direction,
            confidence=confidence,
            sl_pips=round(max(5.0, atr * 1.5), 1),
            tp_pips=round(max(8.0, atr * 2.5), 1),
            timestamp=datetime.now(timezone.utc),
        )
