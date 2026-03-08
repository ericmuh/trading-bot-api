from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_bots() -> dict:
    return {"success": True, "data": []}
