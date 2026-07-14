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
            historical_price.price_date: historical_price
            for historical_price in stored_stock.historical_prices
        }

        for downloaded_price in downloaded_stock.historical_prices:
            stored_price = stored_prices.get(downloaded_price.price_date)
            if stored_price is None:
                stored_stock.historical_prices.append(
                    HistoricalPrice(
                        price=downloaded_price.price,
                        price_date=downloaded_price.price_date,
                    )
                )
            else:
                stored_price.price = downloaded_price.price

        session.commit()
        return stored_stock
