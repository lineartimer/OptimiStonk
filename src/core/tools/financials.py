import asyncio

from core.tools.helpers.edgar import get_financial_info
from core.tools.helpers.yahoo_finance import get_historical_prices


async def get_financials(ticker: str, years: str = 5) -> dict:
    name, price_history = await get_historical_prices(ticker, years)
    financials = await get_financial_info(ticker, years)

    result = {
        "name": name,
        "ticker": ticker,
        "financials": {
            "revenues": financials["revenues"],
            "share_counts": financials["share_counts"]
        },
        "historical_prices": price_history
    }

    return result