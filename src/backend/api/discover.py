from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select

from backend.api.helpers.streamer import stream
from backend.api.stock import get_stock_impl
from backend.core.utils.logger import log_and_stream
from backend.core.utils.message_type import MessageType
from backend.database.database import SessionFactory
from backend.database.models import FailedModel, MarketModel, StockModel


discovery_router = APIRouter()


@discovery_router.get("/api/discover")
async def discover():
    return stream(discover_impl)

async def discover_impl():
    ticker = await _get_random_ticker()

    if not ticker:
        log_and_stream(
            "All the market has been explored. Nothing left to do.",
            MessageType.warning
        )
        raise HTTPException(status_code=404)
    
    log_and_stream(
        f"Information collection started for {ticker}.",
        MessageType.info
    )
    return await get_stock_impl(ticker)


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
