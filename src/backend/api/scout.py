from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select
import structlog

from backend.api.get_stock import get_stock_api
from backend.database.database import SessionFactory
from backend.database.models import Failed, Market, Stock


router = APIRouter()

_logger = structlog.get_logger(__name__)


@router.get("/api/scout")
async def scout():
    ticker = await _get_random_ticker()

    _logger.info("Information collection started.", ticker=ticker)

    if ticker is None:
        _logger.info("All the market has been explored. Nothing left to do.")
        raise HTTPException(status_code=404)

    return await get_stock_api(ticker)


async def _get_random_ticker():
    with SessionFactory() as session:
        ticker = session.scalar(
            select(Market.ticker)
            .where(
                ~select(Stock.id)
                .where(Stock.ticker == Market.ticker)
                .exists(),
                ~select(Failed.ticker)
                .where(Failed.ticker == Market.ticker)
                .exists()
            )
            .order_by(func.random())
            .limit(1)
        )

    return ticker
