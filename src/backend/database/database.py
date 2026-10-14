from sqlalchemy import create_engine, event, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from backend.config import DATABASE_URL
from backend.core.stock import Stock
from backend.database.models import (
    BaseModel,
    FailedModel,
    FilingEmbeddingModel,
    FinancialDataModel,
    HistoricalPriceModel,
    MarketModel,
    StockModel,
    WebPageModel,
    WebSearchModel
)


engine = create_engine(
    DATABASE_URL,
    connect_args=(
        {"check_same_thread": False}
        if make_url(DATABASE_URL).get_backend_name() == "sqlite"
        else {}
    )
)

if engine.dialect.name == "sqlite":
    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys = ON")
        finally:
            cursor.close()


SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)


async def initialize_database() -> None:
    BaseModel.metadata.create_all(bind=engine)

    # Download stock list
    with SessionFactory() as db:
        market_is_populated = db.scalar(
            select(MarketModel.ticker).limit(1)
        ) is not None

    if market_is_populated:
        return
    
    from backend.core.tools.market import Exchange, download_stock_list

    for exchange in (Exchange.nasdaq, Exchange.nyse):
        companies = await download_stock_list(exchange)

        with SessionFactory() as db:
            db.add_all(
                MarketModel(ticker=ticker, **company)
                for ticker, company in companies.items()
            )
            db.commit()


def load_web_page(url: str) -> WebPageModel | None:
    with SessionFactory() as db:
        return db.scalar(select(WebPageModel).where(WebPageModel.url == url))


def save_web_page(url: str, content: str) -> WebPageModel:
    with SessionFactory() as db:
        web_page = WebPageModel(url=url, content=content)

        db.add(web_page)
        db.commit()


def load_web_search(query: str) -> WebSearchModel | None:
    with SessionFactory() as db:
        return db.scalar(
            select(WebSearchModel).where(WebSearchModel.query == query)
        )


def save_web_search(query: str, search_result: list) -> WebSearchModel:
    with SessionFactory() as db:
        brave_search = WebSearchModel(query=query, search_result=search_result)

        db.add(brave_search)
        db.commit()

        return brave_search


def load_stock(ticker: str | None = None) -> Stock | list[Stock] | None:
    with SessionFactory() as db:
        query = select(StockModel).order_by(StockModel.name)
        if ticker:
            query = query.where(StockModel.ticker == ticker.upper())

        companies = []
        for company in db.scalars(query).all():
            financial_rows = list(db.scalars(
                select(FinancialDataModel)
                .where(FinancialDataModel.stock_id == company.id)
                .order_by(FinancialDataModel.quarter)
            ))

            prices = {
                row.quarter: row.price for row in db.scalars(
                    select(HistoricalPriceModel)
                    .where(HistoricalPriceModel.stock_id == company.id)
                )
            }

            financial_rows = [row for row in financial_rows if row.quarter in prices]
            if not financial_rows:
                continue

            companies.append(Stock(
                name=company.name,
                ticker=company.ticker,
                stock_exchange=company.stock_exchange,
                last_price=company.last_price,
                backlog=company.backlog,
                summary=company.summary,
                historical_prices={
                    row.quarter: prices[row.quarter] for row in financial_rows
                },
                **{
                    field: {row.quarter: getattr(row, field) for row in financial_rows}
                    for field in (
                        "revenue",
                        "r_and_d_expense",
                        "operating_income",
                        "net_income",
                        "eps",
                        "cash_and_equivalents",
                        "marketable_securities",
                        "accounts_receivable",
                        "total_assets",
                        "current_liabilities",
                        "long_term_debt",
                        "shareholders_equity",
                        "investment_cash_flow",
                        "share_count"
                    )
                }
            ))

        if not companies:
            return None

        return companies[0] if len(companies) == 1 else companies


def delete_stock(ticker: str) -> bool:
    with SessionFactory() as db:
        stock = db.scalar(
            select(StockModel).where(StockModel.ticker == ticker.strip().upper())
        )

        if stock is None:
            return False

        db.delete(stock)
        db.commit()

        return True


def save_stock(
    company,
    reports: dict[str, str | None],
    embeddings: list[FilingEmbeddingModel]
) -> None:
    
    with SessionFactory() as db:
        ticker = company.ticker.strip().upper()
        company.stock_exchange = db.scalar(
            select(MarketModel.stock_exchange).where(MarketModel.ticker == ticker)
        ) or company.stock_exchange

        stock = StockModel(
            name=company.name,
            ticker=ticker,
            stock_exchange=company.stock_exchange,
            last_price=company.last_price,
            rank=company.rank(),
            backlog=company.backlog,
            price_to_revenue=company.price_to_revenue_ratio(),
            price_to_backlog=company.price_to_backlog_ratio(),
            revenue_growth=company.revenue_growth_per_year(),
            summary=company.summary,
            annual_report=reports["latest_10k"],
            quarterly_report=reports["latest_10q"]
        )
        
        db.add(stock)
        db.flush()

        for quarter, data in company._historical_data.items():
            db.add(FinancialDataModel(
                stock_id=stock.id,
                quarter=quarter,
                revenue=data["revenue"],
                r_and_d_expense=data["r_and_d_expense"],
                operating_income=data["operating_income"],
                net_income=data["net_income"],
                eps=data["eps"],
                cash_and_equivalents=data["cash_and_equivalents"],
                marketable_securities=data["marketable_securities"],
                accounts_receivable=data["accounts_receivable"],
                total_assets=data["total_assets"],
                current_liabilities=data["current_liabilities"],
                long_term_debt=data["long_term_debt"],
                shareholders_equity=data["shareholders_equity"],
                investment_cash_flow=data["investment_cash_flow"],
                share_count=data["share_count"]
            ))

            db.add(HistoricalPriceModel(
                stock_id=stock.id, quarter=quarter, price=data["price"]
            ))

        for embedding in embeddings:
            embedding.stock_id = stock.id
        db.add_all(embeddings)

        db.commit()


def save_failed(ticker: str, reason: str) -> None:
    ticker = ticker.strip().upper()

    with SessionFactory() as db:
        failed = db.get(FailedModel, ticker)
        if failed is None:
            db.add(FailedModel(ticker=ticker, reason=reason))
        else:
            failed.reason = reason

        db.commit()
