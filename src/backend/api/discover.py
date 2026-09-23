from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json
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

    if ticker is None:
        _logger.info("All the market has been explored. Nothing left to do.")
        raise HTTPException(status_code=404)

    async def stream():
        _logger.info("Information collection started.", ticker=ticker)
        yield json.dumps({
            "type": "status",
            "message": f"Information collection started for {ticker}."
        }) + "\n"

        try:
            stock = await get_stock(ticker)
            yield json.dumps({"type": "result", "data": stock}, allow_nan=False) + "\n"
        except HTTPException as error:
            yield json.dumps({
                "type": "error",
                "detail": error.detail,
                "status_code": error.status_code
            }) + "\n"
        except Exception:
            _logger.exception("Discovery failed.", ticker=ticker)
            yield json.dumps({
                "type": "error",
                "detail": "Failed to load stock data.",
                "status_code": 500
            }) + "\n"

    return StreamingResponse(
        stream(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"}
    )


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
