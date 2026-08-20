from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from backend.config import DATABASE_URL
from backend.db.models import (
    Base, FinancialData, HistoricalPrice, Market, Stock, WebPage, WebSearch
)


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)


async def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)

    with SessionFactory() as session:
        market_is_populated = session.scalar(select(Market.ticker).limit(1)) is not None

    if market_is_populated:
        return

    from backend.core.tools.market import download_stock_list
    companies = await download_stock_list()

    with SessionFactory() as session:
        session.add_all(
            Market(
                ticker=ticker,
                company_name=company["company_name"],
                stock_type=company["stock_type"]
            )
            for ticker, company in companies.items()
        )
        session.commit()


def get_web_page(url: str) -> WebPage | None:
    with SessionFactory() as session:
        return session.scalar(select(WebPage).where(WebPage.url == url))


def save_web_page(url: str, content: str) -> WebPage:
    with SessionFactory() as session:
        web_page = WebPage(url=url, content=content)

        session.add(web_page)
        session.commit()


def get_web_search(query: str) -> WebSearch | None:
    with SessionFactory() as session:
        return session.scalar(
            select(WebSearch).where(WebSearch.query == query)
        )


def save_web_search(query: str, search_result: list) -> WebSearch:
    with SessionFactory() as session:
        brave_search = WebSearch(query=query, search_result=search_result)

        session.add(brave_search)
        session.commit()

        return brave_search


def get_stock_data(ticker: str) -> dict | None:
    with SessionFactory() as session:
        stock = session.scalar(select(Stock).where(Stock.ticker == ticker.upper()))
        if stock is None:
            return None

        financial_rows = list(session.scalars(
            select(FinancialData)
            .where(FinancialData.stock_id == stock.id)
            .order_by(FinancialData.quarter)
        ))

        prices = {
            row.quarter: row.price for row in session.scalars(
                select(HistoricalPrice)
                .where(HistoricalPrice.stock_id == stock.id)
            )
        }

        financial_rows = [row for row in financial_rows if row.quarter in prices]
        if not financial_rows:
            return None

        return {
            "name": stock.name,
            "ticker": stock.ticker,
            "last_price": stock.last_price,
            "backlog": stock.backlog,
            "historical_prices": {
                row.quarter: prices[row.quarter] for row in financial_rows
            },
            **{
                field: {row.quarter: getattr(row, field) for row in financial_rows}
                for field in (
                    "revenue", "r_and_d_expense", "investment_cash_flow", "share_count"
                )
            }
        }


def save_stock_data(company, reports: dict) -> None:
    with SessionFactory() as session:
        stock = Stock(
            name=company.name,
            ticker=company.ticker.upper(),
            last_price=company.last_price,
            rank_backlog=company.rank_backlog(),
            rank_market=company.rank_market(),
            backlog=company.backlog,
            price_to_revenue=company.price_to_revenue_ratio(),
            price_to_backlog=company.price_to_backlog_ratio(),
            revenue_growth=company.revenue_growth_per_year(),
            relative_hype=company.relative_hype(),
            annual_report=reports["latest_10k"],
            quarterly_report=reports["latest_10q"]
        )
        session.add(stock)
        session.flush()

        for quarter, data in company._historical_data.items():
            session.add(FinancialData(
                stock_id=stock.id,
                quarter=quarter,
                revenue=data["revenue"],
                r_and_d_expense=data["r_and_d_expense"],
                investment_cash_flow=data["investment_cash_flow"],
                share_count=data["share_count"]
            ))

            session.add(HistoricalPrice(
                stock_id=stock.id, quarter=quarter, price=data["price"]
            ))

        session.commit()
