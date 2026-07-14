import asyncio
import math
from datetime import date
from decimal import Decimal

import yfinance as yf

from database.models import HistoricalPrice, Stock


async def get_stock(ticker: str) -> Stock:
    """Download a stock and its daily closing-price history from Yahoo Finance."""
    normalized_ticker = ticker.strip().upper()
    if not normalized_ticker:
        raise ValueError("Ticker must not be empty")

    return await asyncio.to_thread(_download_stock, normalized_ticker)


def _download_stock(ticker: str) -> Stock:
    yahoo_stock = yf.Ticker(ticker)
    history = yahoo_stock.history(
        period="max",
        interval="1d",
        auto_adjust=False,
        actions=False,
    )

    if history.empty or "Close" not in history.columns:
        raise ValueError(f"No price history found for ticker {ticker}")

    try:
        info = yahoo_stock.get_info()
    except Exception:
        info = {}
    name = info.get("longName") or info.get("shortName") or ticker

    prices_by_date: dict[date, HistoricalPrice] = {}
    for timestamp, row in history.iterrows():
        close = row["Close"]
        try:
            numeric_close = float(close)
        except (TypeError, ValueError):
            continue

        if not math.isfinite(numeric_close) or numeric_close < 0:
            continue

        price_date = timestamp.date()
        prices_by_date[price_date] = HistoricalPrice(
            price=Decimal(str(numeric_close)),
            price_date=price_date,
        )

    if not prices_by_date:
        raise ValueError(f"No valid closing prices found for ticker {ticker}")

    return Stock(
        name=name,
        ticker=ticker,
        historical_prices=list(prices_by_date.values()),
    )
