from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import HistoricalPrice, Stock, engine


def save_stock(downloaded_stock: Stock) -> Stock:
    with Session(engine, expire_on_commit=False) as session:
        stored_stock = session.scalar(
            select(Stock).where(Stock.ticker == downloaded_stock.ticker)
        )

        if stored_stock is None:
            session.add(downloaded_stock)
            session.commit()
            return downloaded_stock

        stored_stock.name = downloaded_stock.name
        stored_prices = {
            historical_price.date: historical_price
            for historical_price in stored_stock.historical_prices
        }

        for downloaded_price in downloaded_stock.historical_prices:
            stored_price = stored_prices.get(downloaded_price.date)
            if stored_price is None:
                stored_stock.historical_prices.append(
                    HistoricalPrice(
                        date=downloaded_price.date,
                        price=downloaded_price.price
                    )
                )
            else:
                stored_price.price = downloaded_price.price

        session.commit()
        return stored_stock
