from __future__ import annotations

from collections import deque


class LatencyMetricsService:
    def __init__(self) -> None:
        self._samples: dict[str, deque[float]] = {}

    def record(self, metric: str, latency_ms: float) -> None:
        bucket = self._samples.setdefault(metric, deque(maxlen=2000))
        bucket.append(max(0.0, float(latency_ms)))

    def snapshot(self) -> dict[str, dict[str, float | int]]:
        output: dict[str, dict[str, float | int]] = {}
        for metric, values in self._samples.items():
            sorted_values = sorted(values)
            if not sorted_values:
                output[metric] = {"count": 0, "p50": 0.0, "p95": 0.0, "p99": 0.0}
                continue
            output[metric] = {
                "count": len(sorted_values),
                "p50": round(self._percentile(sorted_values, 50), 3),
                "p95": round(self._percentile(sorted_values, 95), 3),
                "p99": round(self._percentile(sorted_values, 99), 3),
            }
        return output

    @staticmethod
    def _percentile(values: list[float], percentile: int) -> float:
        if not values:
            return 0.0
        if len(values) == 1:
            return values[0]
        idx = (percentile / 100) * (len(values) - 1)
        low = int(idx)
        high = min(low + 1, len(values) - 1)
        if low == high:
            return values[low]
        weight = idx - low
        return values[low] * (1 - weight) + values[high] * weight


latency_metrics = LatencyMetricsService()
