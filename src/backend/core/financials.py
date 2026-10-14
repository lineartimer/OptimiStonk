from datetime import date

from backend.api.helpers.streamer import stream_message
from backend.core.agents.backlog_finder import BacklogFinder
from backend.core.agents.summarizer import Summarizer
from backend.core.semantic_search import create_embeddings
from backend.core.stock import Stock
from backend.core.tools.brave_search import web_search
from backend.core.tools.edgar import get_financial_data
from backend.core.tools.web import download_web_page
from backend.core.tools.yahoo_finance import get_price_history
from backend.core.utils.message_type import MessageType
from backend.database.database import save_stock


SEARCH_QUERY = "How big is {company_name}'s backlog?"


class NotEnoughDataError(Exception):
    pass


class CompanyLossesError(Exception):
    pass


async def collect_stock_data(ticker: str, years: int = 5) -> Stock:
    ticker = ticker.strip().upper()

    financials, reports = await get_financial_data(ticker, years)

    (
        name,
        last_price,
        price_history,
        extra_price_point
    ) = await get_price_history(ticker, years)

    # If current quarter's 10-Q is not in EDGAR yet,
    # shift price history back one quarter
    if (len(price_history) > 0 and len(financials["revenue"]) > 0 and
        list(price_history)[-1] != list(financials["revenue"])[-1]):
        price_history.popitem()
        quarter, price = extra_price_point.popitem()

        price_history[quarter] = price
        price_history = dict(sorted(price_history.items()))

    # Only keep the intersection of the quarters returned from Yahoo Finance and EDGAR
    common_keys = price_history.keys() & financials["revenue"].keys()
    price_history = {k: price_history[k] for k in common_keys}

    # Taking the intersection discards the order, so order dictionaries again
    price_history = dict(sorted(price_history.items()))

    for field_name in financials.keys():
        financials[field_name] = {
            k: financials[field_name][k] for k in common_keys
        }

        financials[field_name] = dict(
            sorted(financials[field_name].items())
        )

    # Early stopping
    min_quarters = 4 * years - 2 # Subtracting 2 to handle Yahoo Finance vs. Edgar misalignment
    if (len(financials["revenue"]) < min_quarters or
        len(price_history) < min_quarters):
        raise NotEnoughDataError(f"Less than {years} years of data found.")

    financial_data = {
        "name": name,
        "ticker": ticker,
        "last_price": last_price,
        "revenue": financials["revenue"],
        "r_and_d_expense": financials["r_and_d_expense"],
        "operating_income": financials["operating_income"],
        "net_income": financials["net_income"],
        "eps": financials["eps"],
        "cash_and_equivalents": financials["cash_and_equivalents"],
        "marketable_securities": financials["marketable_securities"],
        "accounts_receivable": financials["accounts_receivable"],
        "total_assets": financials["total_assets"],
        "current_liabilities": financials["current_liabilities"],
        "long_term_debt": financials["long_term_debt"],
        "shareholders_equity": financials["shareholders_equity"],
        "investment_cash_flow": financials["investment_cash_flow"],
        "share_count": financials["share_count"],
        "backlog": None,
        "summary": None,
        "historical_prices": price_history
    }

    stock = Stock(**financial_data)

    if stock.price_to_earnings_ratio() < 0:
        raise CompanyLossesError("Company generates losses.")

    # Find out how big the backlog is
    prompt_backlog = {
        "company": name,
        "current_date": date.today().isoformat(),
        "web_pages": []
    }

    cnt = 1
    search_results = await web_search(SEARCH_QUERY.format(company_name=name))

    stream_message("Downloading web pages.", MessageType.info)
    for search_result in search_results:
        if cnt > 5:
            break

        prompt_backlog["web_pages"].append({
            "title": search_result["title"],
            "publish_date": search_result["publish_date"],
            "content": await download_web_page(search_result["url"])
        })
        cnt += 1

        stream_message(".", new_line=False)

    stream_message(f"Finding out how big {name}'s backlog is.", MessageType.info)

    backlog_finder = BacklogFinder()
    stock.backlog = await backlog_finder.run(name, prompt_backlog)

    # Create a summary of the company
    prompt_summarizer = {
        "company": name,
        "latest_10k": reports["latest_10k"],
        "latest_10q": reports["latest_10q"]
    }

    stream_message(
        "Creating a summary based on the latest SEC filings.",
        MessageType.info
    )

    summarizer = Summarizer()
    stock.summary = await summarizer.run(name, prompt_summarizer)

    stream_message("Creating embeddings.", MessageType.info)
    embeddings = await create_embeddings(ticker, reports)

    save_stock(stock, reports, embeddings)
    stream_message("Saved stock to database.", MessageType.info)

    return stock
