from core.tools.helpers.edgar import get_financial_info
from core.tools.helpers.yahoo_finance import get_historical_prices


async def get_financials(ticker: str, years: str = 5) -> dict:
    name, price_history = await get_historical_prices(ticker, years)
    financials = await get_financial_info(ticker, years)

    price_to_revenue = {}
    for quarter in financials["revenue"].keys():
        share_count = financials["share_count"].get(quarter)
        price = price_history.get(quarter)
        revenue = financials["revenue"][quarter]

        if share_count and price:
            price_to_revenue[quarter] = round(share_count * price / (4 * revenue), 2)

    result = {
        "name": name,
        "ticker": ticker,
        "financials": {
            "revenue": financials["revenue"],
            "investment_cash_flow": financials["investment_cash_flow"],
            "number_of_shares_outstanding_assuming_delution": financials["share_count"],
            "price_to_revenue": price_to_revenue
        },
        "historical_prices": price_history
    }

    return result