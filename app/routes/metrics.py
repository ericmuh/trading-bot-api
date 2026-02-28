from __future__ import annotations

from fastapi import APIRouter

from app.services.latency_metrics import latency_metrics

router = APIRouter(tags=["metrics"])


@router.get("/metrics/latency")
def get_latency_metrics() -> dict[str, dict[str, float | int]]:
    return latency_metrics.snapshot()
