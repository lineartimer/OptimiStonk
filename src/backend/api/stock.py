from fastapi import APIRouter, HTTPException, Response
import structlog

from backend.api.helpers.streamer import stream, stream_result
from backend.core.financials import collect_stock_data
from backend.core.stock import StockError
from backend.core.tools.edgar import (
    EdgarParseError,
    EdgarTickerNotFoundError
)
from backend.core.tools.yahoo_finance import (
    YahooFinanceParseError,
    YahooFinanceTickerNotFoundError
)
from backend.core.utils.logger import log_and_stream
from backend.core.utils.message_type import MessageType
from backend.database.database import delete_stock as delete_stock_db, load_stock, save_failed


_logger = structlog.get_logger(__name__)


stock_router = APIRouter()


@stock_router.get("/api/stock")
async def get_stock(ticker: str | None = None):
    return stream(get_stock_impl, ticker)


async def get_stock_impl(ticker: str | None = None):
    ticker = ticker.strip().upper() if ticker else None

    stock = load_stock(ticker)
    if stock:
        log_and_stream(
            f"Stock ({ticker}) loaded from database.",
            MessageType.info
        )

        if isinstance(stock, list):
            return stream_result([item.to_json() for item in stock])
        
        return stream_result(stock.to_json())

    if not ticker:
        return stream_result([])

    try:
        stock = await collect_stock_data(ticker)

    except Exception as e:
        save_failed(ticker, str(e))

        if (isinstance(e, YahooFinanceTickerNotFoundError) or
            isinstance(e, EdgarTickerNotFoundError)):
            status_code = 404
            detail = str(e)

        elif (isinstance(e, YahooFinanceParseError) or
              isinstance(e, EdgarParseError) or
              isinstance(e, StockError)):
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

    return stream_result(stock.to_json())


@stock_router.delete("/api/stock", status_code=204)
def delete_stock(ticker: str):
    ticker = ticker.strip().upper()
    if not ticker:
        raise HTTPException(status_code=422, detail="Ticker is empty.")

    if not delete_stock_db(ticker):
        raise HTTPException(status_code=404, detail=f"Stock ({ticker}) not found.")

    return Response(status_code=204)
