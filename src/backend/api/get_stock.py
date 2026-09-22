from fastapi import APIRouter, HTTPException
import structlog

from backend.core.company import Company
from backend.core.financials import get_stock
from backend.core.tools.edgar import EdgarParseError, EdgarTickerNotFoundError
from backend.core.tools.yahoo_finance import YahooFinanceParseError, YahooFinanceTickerNotFoundError
from backend.database.database import get_company, save_failed_stock


router = APIRouter()


_logger = structlog.get_logger(__name__)


@router.get("/api/stock")
async def get_stock_api(ticker: str):
    ticker = ticker.strip().upper()

    stored_data = get_company(ticker)
    if stored_data:
        _logger.info("Company data loaded from database.", ticker=ticker)
        return Company(**stored_data)

    try:
        stock = await get_stock(ticker)

    except Exception as e:
        save_failed_stock(ticker, str(e))

        if (isinstance(e, YahooFinanceTickerNotFoundError) or
            isinstance(e, EdgarTickerNotFoundError)):
            status_code = 404
            detail = str(e)

        elif (isinstance(e, YahooFinanceParseError) or
              isinstance(e, EdgarParseError)):
            status_code = 422
            detail = str(e)

        else:
            status_code = 500
            detail = "Failed to load stock data."

            _logger.error(detail, error=str(e))

        raise HTTPException(
            status_code=status_code,
            detail=detail
        ) from e

    return stock.to_json()
