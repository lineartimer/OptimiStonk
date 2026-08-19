from fastapi import APIRouter


router = APIRouter()


@router.get("/api/scout")
async def scout():
    return "To do..."
