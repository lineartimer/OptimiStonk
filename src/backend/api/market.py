from fastapi import APIRouter
from sqlalchemy import select

from backend.database.database import SessionFactory
from backend.database.models import FailedModel, MarketModel, StockModel


market_router = APIRouter()


@market_router.get("/api/market")
def get_market() -> list[str]:
    with SessionFactory() as db:
        return list(db.scalars(
            select(MarketModel.ticker)
            .where(
                ~select(StockModel.id)
                .where(StockModel.ticker == MarketModel.ticker)
                .exists(),
                ~select(FailedModel.ticker)
                .where(FailedModel.ticker == MarketModel.ticker)
                .exists()
            )
            .order_by(MarketModel.ticker)
        ))
