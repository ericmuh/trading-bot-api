from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def websocket_status() -> dict:
    return {"success": True, "data": {"enabled": False}}
