from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select

from backend.api.helpers.streamer import MessageType, stream, stream_result
from backend.api.stock import get_stock
from backend.database.database import SessionFactory
from backend.database.models import FailedModel, MarketModel, StockModel
from backend.utils.logger import log_and_stream


discovery_router = APIRouter()


@discovery_router.get("/api/discover")
async def discover():
    return stream(_discover)

async def _discover():
    ticker = await _get_random_ticker()

    if not ticker:
        log_and_stream("All the market has been explored. Nothing left to do.", MessageType.warning)
        raise HTTPException(status_code=404)
    
    log_and_stream(f"Information collection started for {ticker}.", MessageType.info)

    stock = await get_stock(ticker)
    return stream_result(stock)


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
