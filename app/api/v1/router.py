from fastapi import APIRouter

from app.api.v1 import auth, bots, mt5, strategies, trades, users, websocket

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(mt5.router, prefix="/mt5", tags=["mt5"])
api_router.include_router(bots.router, prefix="/bots", tags=["bots"])
api_router.include_router(trades.router, prefix="/trades", tags=["trades"])
api_router.include_router(strategies.router, prefix="/strategies", tags=["strategies"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])
