from __future__ import annotations
from sqlalchemy import Float, ForeignKey, JSON, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class BaseModel(DeclarativeBase):
    pass


class WebPageModel(BaseModel):
    __tablename__ = "web_pages"

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(Text, unique=True, index=True)
    content: Mapped[str] = mapped_column(Text)


class WebSearchModel(BaseModel):
    __tablename__ = "web_searches"

    id: Mapped[int] = mapped_column(primary_key=True)
    query: Mapped[str] = mapped_column(Text, unique=True, index=True)
    search_result: Mapped[list] = mapped_column(JSON)


class MarketModel(BaseModel):
    __tablename__ = "market"

    ticker: Mapped[str] = mapped_column(Text, primary_key=True)
    company_name: Mapped[str] = mapped_column(Text)
    stock_type: Mapped[str] = mapped_column(Text)


class FailedModel(BaseModel):
    __tablename__ = "failed"

    ticker: Mapped[str] = mapped_column(Text, primary_key=True)
    reason: Mapped[str] = mapped_column(Text)


class StockModel(BaseModel):
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    ticker: Mapped[str] = mapped_column(Text, unique=True, index=True)
    last_price: Mapped[float] = mapped_column(Float)
    rank_market: Mapped[float | None] = mapped_column(Float, nullable=True)
    rank_backlog: Mapped[float | None] = mapped_column(Float, nullable=True)
    backlog: Mapped[int | None] = mapped_column(nullable=True)
    price_to_revenue: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_to_backlog: Mapped[float | None] = mapped_column(Float, nullable=True)
    revenue_growth: Mapped[float | None] = mapped_column(Float, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    annual_report: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    quarterly_report: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    financial_data: Mapped[list[FinancialDataModel]] = relationship(
        back_populates="stock", cascade="all, delete-orphan"
    )

    historical_prices: Mapped[list[HistoricalPriceModel]] = relationship(
        back_populates="stock", cascade="all, delete-orphan"
    )


class FinancialDataModel(BaseModel):
    __tablename__ = "financial_data"
    __table_args__ = (UniqueConstraint("stock_id", "quarter"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[int] = mapped_column(
        ForeignKey("stocks.id", ondelete="CASCADE"), index=True
    )
    
    quarter: Mapped[str] = mapped_column(Text)
    revenue: Mapped[int]
    r_and_d_expense: Mapped[int]
    operating_income: Mapped[int | None] = mapped_column(nullable=True)
    cash_and_equivalents: Mapped[int | None] = mapped_column(nullable=True)
    marketable_securities: Mapped[int | None] = mapped_column(nullable=True)
    accounts_receivable: Mapped[int | None] = mapped_column(nullable=True)
    total_assets: Mapped[int | None] = mapped_column(nullable=True)
    investment_cash_flow: Mapped[int]
    share_count: Mapped[int]

    stock: Mapped[StockModel] = relationship(back_populates="financial_data")


class HistoricalPriceModel(BaseModel):
    __tablename__ = "historical_prices"
    __table_args__ = (UniqueConstraint("stock_id", "quarter"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[int] = mapped_column(
        ForeignKey("stocks.id", ondelete="CASCADE"), index=True
    )

    quarter: Mapped[str] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Float)

    stock: Mapped[StockModel] = relationship(back_populates="historical_prices")
