from fastapi import APIRouter

from backend.core.financials import get_financials

router = APIRouter()

@router.get("/api/stock")
async def get_stock(ticker: str):
    ticker = ticker.strip().upper()
    stock = await get_financials(ticker)

    return stock.to_json()
