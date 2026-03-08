from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_trades() -> dict:
    return {"success": True, "data": []}
