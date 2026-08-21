from fastapi import APIRouter, HTTPException

from backend.core.financials import get_financials
from backend.core.tools.edgar import EdgarDataLessThanTwoQuartersError, EdgarParseError, EdgarTickerNotFoundError
from backend.core.tools.yahoo_finance import YahooFinanceDataLessThanTwoQuartersError, YahooFinanceTickerNotFoundError
from backend.db.database import save_failed_stock


router = APIRouter()


@router.get("/api/stock")
async def get_stock(ticker: str):
    ticker = ticker.strip().upper()

    try:
        stock = await get_financials(ticker)

    except Exception as e:
        save_failed_stock(ticker, str(e))

        if (isinstance(e, YahooFinanceTickerNotFoundError) or
            isinstance(e, EdgarTickerNotFoundError)):
            status_code = 404
            detail = str(e)

        elif (isinstance(e, YahooFinanceDataLessThanTwoQuartersError) or
              isinstance(e, EdgarParseError) or
              isinstance(e, EdgarDataLessThanTwoQuartersError)):
            status_code = 422
            detail = str(e)

        else:
            status_code = 500
            detail = "Failed to load stock data."

        raise HTTPException(
            status_code=status_code,
            detail=detail
        ) from e

    return stock.to_json()
