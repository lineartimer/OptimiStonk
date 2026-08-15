from core.agents.backlog_extractor import BacklogExtractor
from core.tools.helpers.edgar import get_stock_info
from core.tools.helpers.yahoo_finance import get_price_history


async def get_financials(ticker: str, years: str = 5) -> dict:
    name, last_price, price_history = await get_price_history(ticker, years)
    financials, sec_filings = await get_stock_info(ticker, years)

    price_to_revenue = {}
    for quarter in financials["revenue"].keys():
        share_count = financials["share_count"].get(quarter)
        price = price_history.get(quarter)
        revenue = financials["revenue"][quarter]

        if share_count and price:
            current_price_to_revenue = round(share_count * last_price / (4 * revenue), 2)
            price_to_revenue[quarter] = round(share_count * price / (4 * revenue), 2)

    latest_10k = sec_filings["latest_10k"]
    latest_10q = sec_filings["latest_10q"]
    
    backlog_extractor = BacklogExtractor()
    backlog = await backlog_extractor.run(
        name,
        latest_10k["document"] if latest_10k["date"] > latest_10q["date"] else "",
        latest_10q["document"] if latest_10q["date"] > latest_10k["date"] else ""
    )

    result = {
        "name": name,
        "ticker": ticker,
        "last_price": last_price,
        "current_price_to_revenue": current_price_to_revenue,
        "financials": {
            "revenue": financials["revenue"],
            "r_and_d_expense": financials["r_and_d_expense"],
            "investment_cash_flow": financials["investment_cash_flow"],
            "number_of_shares_outstanding_assuming_delution": financials["share_count"],
            "price_to_revenue": price_to_revenue
        },
        "backlog": backlog,
        "historical_prices": price_history
    }

    return result
