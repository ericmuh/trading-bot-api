from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.db.store import init_db, stop_all_running_bots
from app.routes.dashboard import router as dashboard_router
from app.routes.license import router as license_router
from app.routes.metrics import router as metrics_router
from app.routes.mt5 import router as mt5_router
from app.routes.risk import router as risk_router
from app.routes.trading import router as trading_router

app = FastAPI(
    title="Trading Bot Backend API",
    version="0.1.0",
    description="API for MT5 trading bot automation, risk controls, licensing, and monitoring.",
    docs_url="/swagger",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

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


@app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
def root_redirect() -> RedirectResponse:
    return RedirectResponse(url="/swagger", status_code=307)


@app.exception_handler(StarletteHTTPException)
async def redirect_not_found_to_docs(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return RedirectResponse(url="/swagger", status_code=307)
    return await http_exception_handler(request, exc)


@app.get("/health")
def health() -> dict:
    return {"ok": True}


app.include_router(mt5_router)
app.include_router(risk_router)
app.include_router(trading_router)
app.include_router(dashboard_router)
app.include_router(license_router)
app.include_router(metrics_router)
