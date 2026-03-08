from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_strategies() -> dict:
    return {"success": True, "data": []}
