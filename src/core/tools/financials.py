import asyncio

from core.tools.helpers.edgar import get_financial_info
from core.tools.helpers.yahoo_finance import get_historical_prices
from database.database import save_stock


async def get_financials(ticker: str, years: str = 5) -> dict:
    price_history = await get_historical_prices(ticker)
    stock = await asyncio.to_thread(save_stock, price_history)

    financials = await get_financial_info(ticker, years)

    result = {
        "name": stock.name,
        "ticker": stock.ticker,
        "financials": {
            "revenues": financials["quarterly"]["revenues"],
            "share_counts": financials["quarterly"]["share_counts"]
        },
        "historical_prices": [
            {
                "date": price_point.date,
                "price": price_point.price
            }
            for price_point in stock.historical_prices
        ]
    }

    return result