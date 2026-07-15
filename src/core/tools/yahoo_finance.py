import asyncio
from decimal import Decimal
import structlog
import yfinance as yf

from database.models import HistoricalPrice, Stock, round_price


_logger = structlog.get_logger(__name__)


async def get_historical_prices(ticker: str) -> Stock:
    """
        Download historical prices of the given stock from Yahoo Finance.
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
            numeric_close = Decimal(str(close))
        except Exception:
            continue

        if not numeric_close.is_finite() or numeric_close < 0:
            continue

        date = timestamp.date()
        prices_by_date[date] = HistoricalPrice(
            date=date,
            price=round_price(numeric_close)
        )
    
    _logger.info(f"Downloaded price data for {ticker} from Yahoo Finance.")

    return Stock(
        name=name,
        ticker=ticker,
        historical_prices=list(prices_by_date.values())
    )