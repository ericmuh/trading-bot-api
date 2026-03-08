from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio

from app.api.middleware.logging import LoggingMiddleware
from app.api.v1.websocket import sio, start_redis_listener_task
from app.api.v1.router import api_router
from app.core.database import init_db
from app.core.events import shutdown_services
from app.core.exceptions import AppException, app_exception_handler
from app.core.redis import init_redis


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    redis_ready = await init_redis()
    listener_task = start_redis_listener_task() if redis_ready else None
    yield
    if listener_task:
        listener_task.cancel()
    await shutdown_services()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Trading Platform API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LoggingMiddleware)

    app.add_exception_handler(AppException, app_exception_handler)
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health")
    async def health() -> dict:
        return {
            "success": True,
            "data": {"status": "ok"},
        }

    return app


app = create_app()
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)
