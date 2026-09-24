from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select
import structlog

from backend.api.helpers.streamer import stream, stream_result, stream_status
from backend.api.stock import get_stock
from backend.database.database import SessionFactory
from backend.database.models import FailedModel, MarketModel, StockModel


discovery_router = APIRouter()

_logger = structlog.get_logger(__name__)


@discovery_router.get("/api/discover")
async def discover():
    return stream(_discover())

async def _discover():
    ticker = await _get_random_ticker()

    if ticker is None:
        _logger.info("All the market has been explored. Nothing left to do.")
        raise HTTPException(status_code=404)
    
    _logger.info("Information collection started.", ticker=ticker)
    yield stream_status(f"Information collection started for {ticker}.")

    stock = await get_stock(ticker)
    yield stream_result(stock)


async def _get_random_ticker():
    with SessionFactory() as session:
        ticker = session.scalar(
            select(MarketModel.ticker)
            .where(
                ~select(StockModel.id)
                .where(StockModel.ticker == MarketModel.ticker)
                .exists(),
                ~select(FailedModel.ticker)
                .where(FailedModel.ticker == MarketModel.ticker)
                .exists()
            )
            .order_by(func.random())
            .limit(1)
        )

    return ticker
