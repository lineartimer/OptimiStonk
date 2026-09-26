from fastapi import APIRouter, HTTPException
import structlog

from backend.core.financials import collect_stock_data
from backend.core.tools.edgar import (
    EdgarParseError,
    EdgarTickerNotFoundError
)
from backend.core.tools.yahoo_finance import (
    YahooFinanceParseError,
    YahooFinanceTickerNotFoundError
)
from backend.database.database import load_stock, save_failed


stock_router = APIRouter()


_logger = structlog.get_logger(__name__)


@stock_router.get("/api/stock")
async def get_stock(ticker: str | None = None):
    ticker = ticker.strip().upper() if ticker else None

    stock = load_stock(ticker)
    if stock:
        _logger.info("Company data loaded from database.", ticker=ticker)
        if isinstance(stock, list):
            return [item.to_json() for item in stock]
        
        return stock.to_json()

    if not ticker:
        return []

    try:
        stock = await collect_stock_data(ticker)

    except Exception as e:
        save_failed(ticker, str(e))

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
