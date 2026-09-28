from fastapi import APIRouter
from sqlalchemy import select

from backend.database.database import SessionFactory
from backend.database.models import MarketModel


market_router = APIRouter()


@market_router.get("/api/market")
def get_market() -> list[str]:
    with SessionFactory() as session:
        return list(session.scalars(
            select(MarketModel.ticker).order_by(MarketModel.ticker)
        ))
