from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select
import structlog

from backend.api.stock import get_stock
from backend.database.database import SessionFactory
from backend.database.models import FailedModel, MarketModel, StockModel


discovery_router = APIRouter()

_logger = structlog.get_logger(__name__)


@discovery_router.get("/api/discover")
async def discover():
    ticker = await _get_random_ticker()

    _logger.info("Information collection started.", ticker=ticker)

    if ticker is None:
        _logger.info("All the market has been explored. Nothing left to do.")
        raise HTTPException(status_code=404)

    return await get_stock(ticker)


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
