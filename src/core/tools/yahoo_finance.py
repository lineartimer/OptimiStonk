import asyncio
import math
from decimal import Decimal

import yfinance as yf

from database.models import HistoricalPrice, Stock


async def get_stock(ticker: str) -> Stock:
    """
        Download historical prices about a stock from Yahoo Finance.
    """

    return await asyncio.to_thread(
        _download_stock,
        ticker.strip().upper()
    )


def _download_stock(ticker: str) -> Stock:
    stock = yf.Ticker(ticker)
    price_history = stock.history(
        period="max",
        interval="1wk",
        auto_adjust=False,
        actions=True
    )

    try:
        info = stock.get_info()
    except Exception:
        info = {}
    
    name = info.get("longName") or info.get("shortName") or ticker

    prices_by_date = {}
    for timestamp, row in price_history.iterrows():
        close = row["Close"]

        try:
            numeric_close = float(close)
        except Exception:
            continue

        if not math.isfinite(numeric_close) or numeric_close < 0:
            continue

        price_date = timestamp.date()
        prices_by_date[price_date] = HistoricalPrice(
            price=Decimal(str(numeric_close)),
            price_date=price_date
        )

    if not prices_by_date:
        raise ValueError(f"No valid closing prices found for ticker {ticker}")

    return Stock(
        name=name,
        ticker=ticker,
        historical_prices=list(prices_by_date.values())
    )
