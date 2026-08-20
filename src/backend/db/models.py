from __future__ import annotations

from sqlalchemy import Float, ForeignKey, JSON, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class WebPage(Base):
    __tablename__ = "web_pages"

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(Text, unique=True, index=True)
    content: Mapped[str] = mapped_column(Text)


class WebSearch(Base):
    __tablename__ = "web_searches"

    id: Mapped[int] = mapped_column(primary_key=True)
    query: Mapped[str] = mapped_column(Text, unique=True, index=True)
    search_result: Mapped[list] = mapped_column(JSON)


class Market(Base):
    __tablename__ = "market"

    ticker: Mapped[str] = mapped_column(Text, primary_key=True)
    company_name: Mapped[str] = mapped_column(Text)
    stock_type: Mapped[str] = mapped_column(Text)


class Failed(Base):
    __tablename__ = "failed"

    ticker: Mapped[str] = mapped_column(Text, primary_key=True)
    reason: Mapped[str] = mapped_column(Text)


class Stock(Base):
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    ticker: Mapped[str] = mapped_column(Text, unique=True, index=True)
    last_price: Mapped[float] = mapped_column(Float)
    rank_market: Mapped[float] = mapped_column(Float)
    rank_backlog: Mapped[float] = mapped_column(Float)
    backlog: Mapped[int]
    price_to_revenue: Mapped[float] = mapped_column(Float)
    price_to_backlog: Mapped[float] = mapped_column(Float)
    revenue_growth: Mapped[float] = mapped_column(Float)
    relative_hype: Mapped[float] = mapped_column(Float)
    annual_report: Mapped[dict] = mapped_column(JSON)
    quarterly_report: Mapped[dict] = mapped_column(JSON)

    financial_data: Mapped[list[FinancialData]] = relationship(
        back_populates="stock", cascade="all, delete-orphan"
    )

    historical_prices: Mapped[list[HistoricalPrice]] = relationship(
        back_populates="stock", cascade="all, delete-orphan"
    )


class FinancialData(Base):
    __tablename__ = "financial_data"
    __table_args__ = (UniqueConstraint("stock_id", "quarter"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), index=True)
    quarter: Mapped[str] = mapped_column(Text)
    revenue: Mapped[int]
    r_and_d_expense: Mapped[int]
    investment_cash_flow: Mapped[int]
    share_count: Mapped[int]

    stock: Mapped[Stock] = relationship(back_populates="financial_data")


class HistoricalPrice(Base):
    __tablename__ = "historical_prices"
    __table_args__ = (UniqueConstraint("stock_id", "quarter"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), index=True)
    quarter: Mapped[str] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Float)

    stock: Mapped[Stock] = relationship(back_populates="historical_prices")
