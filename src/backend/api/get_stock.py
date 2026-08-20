from fastapi import APIRouter

from backend.core.financials import get_financials
from backend.db.database import save_failed_stock


router = APIRouter()


@router.get("/api/stock")
async def get_stock(ticker: str):
    ticker = ticker.strip().upper()
    try:
        stock = await get_financials(ticker)
    except Exception as error:
        save_failed_stock(ticker, str(error))
        raise

    return stock.to_json()
