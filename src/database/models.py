from __future__ import annotations

import sqlite3
from datetime import date as DateValue
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    create_engine,
    event
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    validates,
)


DATABASE_PATH = Path(__file__).with_name("database.db")
engine = create_engine(f"sqlite:///{DATABASE_PATH}")
PRICE_PRECISION = 20
PRICE_SCALE = 2
PRICE_QUANTUM = Decimal("0.01")


def round_price(price: Decimal) -> Decimal:
    return price.quantize(PRICE_QUANTUM, rounding=ROUND_HALF_UP)


@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(
    dbapi_connection: sqlite3.Connection, _: Any
) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()


class Base(DeclarativeBase):
    pass


class Stock(Base):
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)

    historical_prices: Mapped[list[HistoricalPrice]] = relationship(
        back_populates="stock",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


class HistoricalPrice(Base):
    __tablename__ = "historical_prices"
    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_historical_prices_price_nonnegative"),
        UniqueConstraint(
            "stock_id",
            "date",
            name="uq_historical_prices_stock_date"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[int] = mapped_column(
        ForeignKey("stocks.id", ondelete="CASCADE"),
        nullable=False
    )
    date: Mapped[DateValue] = mapped_column(Date, nullable=False)
    price: Mapped[Decimal] = mapped_column(
        Numeric(PRICE_PRECISION, PRICE_SCALE),
        nullable=False,
    )

    stock: Mapped[Stock] = relationship(back_populates="historical_prices")

    @validates("price")
    def _round_price(self, _: str, price: Decimal) -> Decimal:
        return round_price(price)


def create_database() -> None:
    Base.metadata.create_all(engine)
