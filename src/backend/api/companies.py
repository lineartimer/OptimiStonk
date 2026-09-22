from fastapi import APIRouter
from sqlalchemy import func, select

from backend.database.database import SessionFactory
from backend.database.models import Stock


router = APIRouter()


@router.get("/api/companies")
def get_companies():
    with SessionFactory() as session:
        companies = session.execute(
            select(Stock.name, Stock.ticker, Stock.summary)
            .order_by(func.lower(Stock.name), Stock.ticker)
        ).mappings()

        return [dict(company) for company in companies]
