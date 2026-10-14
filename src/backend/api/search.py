from fastapi import APIRouter

from backend.core.semantic_search import rag as rag_impl


search_router = APIRouter()


@search_router.get("/api/rag")
async def rag(query: str) -> dict:
    return await rag_impl(query)
