from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import sqrt


@dataclass
class AIDecision:
    approved: bool
    confidence: float
    reasons: list[str]
    trend_strength: float
    volatility: float


class AIFilterService:
    def __init__(self) -> None:
        self._price_windows: dict[tuple[str, str], deque[float]] = {}

    def evaluate(
        self,
        *,
        user_id: str,
        symbol: str,
        price: float,
        news_spike: bool,
        confidence_threshold: float,
    ) -> AIDecision:
        window = self._price_windows.setdefault((user_id, symbol), deque(maxlen=20))
        window.append(price)

        if news_spike:
            return AIDecision(
                approved=False,
                confidence=0.0,
                reasons=["blocked_by_news_spike"],
                trend_strength=0.0,
                volatility=0.0,
            )

        trend_strength = self._trend_strength(window)
        volatility = self._volatility(window)

        reasons: list[str] = []
        if trend_strength >= 0.00012:
            reasons.append("trend_strength_ok")
        else:
            reasons.append("trend_strength_weak")

        volatility_spike = volatility >= 0.0018
        if volatility_spike:
            reasons.append("volatility_spike_detected")
        else:
            reasons.append("volatility_normal")

        confidence = max(0.0, min(1.0, (trend_strength * 1800) + (0.5 if not volatility_spike else 0.15)))

        approved = confidence >= confidence_threshold and not volatility_spike
        if not approved:
            reasons.append("rejected_below_threshold")

        return AIDecision(
            approved=approved,
            confidence=round(confidence, 6),
            reasons=reasons,
            trend_strength=round(trend_strength, 8),
            volatility=round(volatility, 8),
        )

    @staticmethod
    def _trend_strength(window: deque[float]) -> float:
        if len(window) < 3:
            return 0.0
        first = window[0]
        last = window[-1]
        if first == 0:
            return 0.0
        return abs((last - first) / first)

    @staticmethod
    def _volatility(window: deque[float]) -> float:
        if len(window) < 4:
            return 0.0

        returns: list[float] = []
        prices = list(window)
        for idx in range(1, len(prices)):
            prev = prices[idx - 1]
            curr = prices[idx]
            if prev == 0:
                continue
            returns.append((curr - prev) / prev)

        if len(returns) < 2:
            return 0.0

        mean = sum(returns) / len(returns)
        variance = sum((item - mean) ** 2 for item in returns) / len(returns)
        return sqrt(variance)
