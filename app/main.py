from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.store import init_db, stop_all_running_bots
from app.routes.dashboard import router as dashboard_router
from app.routes.license import router as license_router
from app.routes.metrics import router as metrics_router
from app.routes.mt5 import router as mt5_router
from app.routes.risk import router as risk_router
from app.routes.trading import router as trading_router

app = FastAPI(title="Trading Bot Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.on_event("shutdown")
def on_shutdown() -> None:
    stop_all_running_bots()


@app.get("/health")
def health() -> dict:
    return {"ok": True}


app.include_router(mt5_router)
app.include_router(risk_router)
app.include_router(trading_router)
app.include_router(dashboard_router)
app.include_router(license_router)
app.include_router(metrics_router)
