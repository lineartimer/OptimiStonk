from datetime import date
import structlog

from backend.core.agents.backlog_finder import BacklogFinder
from backend.core.agents.summarizer import Summarizer
from backend.core.company import Company
from backend.core.tools.brave_search import web_search
from backend.core.tools.edgar import get_financial_data
from backend.core.tools.web import load_web_page
from backend.core.tools.yahoo_finance import get_price_history
from backend.database.database import get_stock_data, save_stock_data


_logger = structlog.get_logger(__name__)

SEARCH_QUERY = "How big is {company_name}'s backlog?"


async def get_stock(ticker: str, years: int = 5) -> Company:
    ticker = ticker.strip().upper()

    stored_data = get_stock_data(ticker)
    if stored_data:
        _logger.info("Company data loaded from database.", ticker=ticker)
        return Company(**stored_data)

    name, last_price, price_history, extra_price_point = await get_price_history(ticker, years)
    financials, reports = await get_financial_data(ticker, years)

    # If current quarter's 10-Q is not in EDGAR yet, shift price history back one quarter
    if (len(price_history) > 0 and len(financials["revenue"]) > 0 and
        list(price_history)[-1] != list(financials["revenue"])[-1]):
        price_history.popitem()
        quarter, price = extra_price_point.popitem()

        price_history[quarter] = price
        price_history = dict(sorted(price_history.items()))

    # Only keep the intersection of the quarters returned from Yahoo Finance and EDGAR
    common_keys = price_history.keys() & financials["revenue"].keys()

    price_history = {k: price_history[k] for k in common_keys}

    financials["revenue"] = {k: financials["revenue"][k] for k in common_keys}
    financials["r_and_d_expense"] = {k: financials["r_and_d_expense"][k] for k in common_keys}
    financials["share_count"] = {k: financials["share_count"][k] for k in common_keys}
    financials["investment_cash_flow"] = {k: financials["investment_cash_flow"][k] for k in common_keys}

    # Taking the intersection discards the order, so order dictionaries again
    price_history = dict(sorted(price_history.items()))

    financials["revenue"] = dict(sorted(financials["revenue"].items()))
    financials["r_and_d_expense"] = dict(sorted(financials["r_and_d_expense"].items()))
    financials["share_count"] = dict(sorted(financials["share_count"].items()))
    financials["investment_cash_flow"] = dict(sorted(financials["investment_cash_flow"].items()))

    # Find out how big the backlog is
    prompt_backlog = {
        "company": name,
        "current_date": date.today().isoformat(),
        "web_pages": []
    }

    cnt = 1
    search_results = await web_search(SEARCH_QUERY.format(company_name=name))
    for search_result in search_results:
        if cnt > 5:
            break

        prompt_backlog["web_pages"].append({
            "title": search_result["title"],
            "publish_date": search_result["publish_date"],
            "content": await load_web_page(search_result["url"])
        })
        cnt += 1

    backlog_finder = BacklogFinder()
    backlog = await backlog_finder.run(name, prompt_backlog)

    # Create a summary of the company
    prompt_summarizer = {
        "company": name,
        "latest_10k": reports["latest_10k"]["document"],
        "latest_10q": reports["latest_10q"]["document"]
    }

    summarizer = Summarizer()
    summary = await summarizer.run(name, prompt_summarizer)

    financial_data = {
        "name": name,
        "ticker": ticker,
        "last_price": last_price,
        "revenue": financials["revenue"],
        "r_and_d_expense": financials["r_and_d_expense"],
        "investment_cash_flow": financials["investment_cash_flow"],
        "share_count": financials["share_count"],
        "backlog": backlog,
        "summary": summary,
        "historical_prices": price_history
    }

    company = Company(**financial_data)
    save_stock_data(company, reports)

    return company
