import asyncio
import json

import socketio
from fastapi import APIRouter

from app.core.redis import get_redis
from app.core.security import decode_token

router = APIRouter()

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")


@router.get("/status")
async def websocket_status() -> dict:
    return {"success": True, "data": {"enabled": True}}


@sio.event
async def connect(sid, environ, auth):  # noqa: ANN001
    token = (auth or {}).get("token")
    if not token:
        raise socketio.exceptions.ConnectionRefusedError("No token")
    try:
        payload = decode_token(token)
        await sio.save_session(sid, {"user_id": payload["sub"]})
    except ValueError as error:
        raise socketio.exceptions.ConnectionRefusedError("Invalid token") from error


@sio.event
async def subscribe_bot(sid, data):  # noqa: ANN001
    bot_id = (data or {}).get("bot_id")
    if bot_id:
        await sio.enter_room(sid, f"bot:{bot_id}")


@sio.event
async def unsubscribe_bot(sid, data):  # noqa: ANN001
    bot_id = (data or {}).get("bot_id")
    if bot_id:
        await sio.leave_room(sid, f"bot:{bot_id}")


@sio.event
async def disconnect(sid):  # noqa: ANN001
    return None


async def redis_listener():
    redis = await get_redis()
    pubsub = redis.pubsub()
    await pubsub.psubscribe("bot:events:*")
    async for message in pubsub.listen():
        if message["type"] == "pmessage":
            channel = message["channel"]
            if isinstance(channel, bytes):
                channel = channel.decode("utf-8")
            bot_id = channel.split(":")[-1]
            payload = message["data"]
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            data = json.loads(payload)
            await sio.emit(data["event"], data["payload"], room=f"bot:{bot_id}")


def start_redis_listener_task() -> asyncio.Task:
    return asyncio.create_task(redis_listener())

