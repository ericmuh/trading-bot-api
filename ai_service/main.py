from datetime import datetime, timezone

import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel

from app.ai.signal_scorer import SignalScorer
from app.ai.trend_detector import TrendDetector
from app.ai.volatility_analyser import VolatilityAnalyser

app = FastAPI(title="AI Analysis Service")
scorer = SignalScorer()
trend_detector = TrendDetector()
vol_analyser = VolatilityAnalyser()


class SignalRequest(BaseModel):
    symbol: str
    ohlcv: list[dict]
    strategy_id: str | None = None


@app.post("/ai/signal")
async def get_signal(req: SignalRequest):
    data_frame = pd.DataFrame(req.ohlcv)
    data_frame.attrs["symbol"] = req.symbol
    signal = scorer.score(data_frame, req.symbol)
    trend = trend_detector.detect(data_frame)
    vol = vol_analyser.analyse(data_frame)
    return {
        "direction": signal.direction.value,
        "confidence": signal.confidence,
        "sl_pips": signal.sl_pips * vol.sl_multiplier,
        "tp_pips": signal.tp_pips * vol.tp_multiplier,
        "trend": trend.direction.value,
        "volatility_regime": vol.regime.value,
        "timestamp": signal.timestamp.isoformat(),
    }


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}
