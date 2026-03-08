from datetime import datetime

import httpx

from app.ai.signal_scorer import Direction, Signal
from app.config import settings


class AIService:
    async def get_signal(self, ohlcv, strategy_id: str) -> Signal:
        payload = {
            "symbol": ohlcv.attrs.get("symbol", "EURUSD"),
            "ohlcv": ohlcv.to_dict(orient="records"),
            "strategy_id": strategy_id,
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(f"{settings.AI_SERVICE_URL}/ai/signal", json=payload)
            response.raise_for_status()
            data = response.json()

        return Signal(
            direction=Direction(data["direction"]),
            confidence=float(data["confidence"]),
            sl_pips=float(data["sl_pips"]),
            tp_pips=float(data["tp_pips"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )
