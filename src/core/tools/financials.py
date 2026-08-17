from datetime import date

from core.agents.backlog_finder import BacklogFinder
from core.tools.brave_search import web_search
from core.tools.helpers.edgar import get_stock_info
from core.tools.helpers.yahoo_finance import get_price_history
from core.tools.web import load_web_page


async def get_financials(ticker: str, years: str = 5) -> dict:
    name, last_price, price_history = await get_price_history(ticker, years)
    financials, _ = await get_stock_info(ticker, years)

    price_to_revenue = {}
    for quarter in financials["revenue"].keys():
        share_count = financials["share_count"].get(quarter)
        price = price_history.get(quarter)
        revenue = financials["revenue"][quarter]

        if share_count and price:
            current_price_to_revenue = round(share_count * last_price / (4 * revenue), 2)
            price_to_revenue[quarter] = round(share_count * price / (4 * revenue), 2)

    prompt = {
        "company": name,
        "current_date": date.today().isoformat(),
        "web_pages": []
    }

    cnt = 1
    search_results = await web_search(f"How big is {name}'s backlog?")
    for search_result in search_results:
        if cnt > 5:
            break

        prompt["web_pages"].append({
            "title": search_result["title"],
            "publish_date": search_result["publish_date"],
            "content": await load_web_page(search_result["url"])
        })
        cnt += 1

    backlog_finder = BacklogFinder()
    backlog = await backlog_finder.run(name, prompt)

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
