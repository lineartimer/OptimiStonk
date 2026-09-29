from datetime import date

from backend.api.helpers.streamer import stream_message
from backend.core.agents.backlog_finder import BacklogFinder
from backend.core.agents.summarizer import Summarizer
from backend.core.stock import Stock
from backend.core.tools.brave_search import web_search
from backend.core.tools.edgar import get_financial_data
from backend.core.tools.web import download_web_page
from backend.core.tools.yahoo_finance import get_price_history
from backend.core.utils.message_type import MessageType
from backend.database.database import save_stock


SEARCH_QUERY = "How big is {company_name}'s backlog?"


async def collect_stock_data(ticker: str, years: int = 5) -> Stock:
    ticker = ticker.strip().upper()

    (
        name,
        last_price,
        price_history,
        extra_price_point
    ) = await get_price_history(ticker, years)

    financials, reports = await get_financial_data(ticker, years)

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

    financials["revenue"] = {
        k: financials["revenue"][k] for k in common_keys
    }
    financials["r_and_d_expense"] = {
        k: financials["r_and_d_expense"][k] for k in common_keys
    }
    financials["operating_income"] = {
        k: financials["operating_income"][k] for k in common_keys
    }
    financials["cash_and_equivalents"] = {
        k: financials["cash_and_equivalents"][k] for k in common_keys
    }
    financials["marketable_securities"] = {
        k: financials["marketable_securities"][k] for k in common_keys
    }
    financials["accounts_receivable"] = {
        k: financials["accounts_receivable"][k] for k in common_keys
    }
    financials["total_assets"] = {
        k: financials["total_assets"][k] for k in common_keys
    }
    financials["current_liabilities"] = {
        k: financials["current_liabilities"][k] for k in common_keys
    }
    financials["long_term_debt"] = {
        k: financials["long_term_debt"][k] for k in common_keys
    }
    financials["shareholders_equity"] = {
        k: financials["shareholders_equity"][k] for k in common_keys
    }
    financials["share_count"] = {
        k: financials["share_count"][k] for k in common_keys
    }
    financials["investment_cash_flow"] = {
        k: financials["investment_cash_flow"][k] for k in common_keys
    }

    # Taking the intersection discards the order, so order dictionaries again
    price_history = dict(sorted(price_history.items()))

    financials["revenue"] = dict(
        sorted(financials["revenue"].items())
    )
    financials["r_and_d_expense"] = dict(
        sorted(financials["r_and_d_expense"].items())
    )
    financials["operating_income"] = dict(
        sorted(financials["operating_income"].items())
    )
    financials["cash_and_equivalents"] = dict(
        sorted(financials["cash_and_equivalents"].items())
    )
    financials["marketable_securities"] = dict(
        sorted(financials["marketable_securities"].items())
    )
    financials["accounts_receivable"] = dict(
        sorted(financials["accounts_receivable"].items())
    )
    financials["total_assets"] = dict(
        sorted(financials["total_assets"].items())
    )
    financials["current_liabilities"] = dict(
        sorted(financials["current_liabilities"].items())
    )
    financials["long_term_debt"] = dict(
        sorted(financials["long_term_debt"].items())
    )
    financials["shareholders_equity"] = dict(
        sorted(financials["shareholders_equity"].items())
    )
    financials["share_count"] = dict(
        sorted(financials["share_count"].items())
    )
    financials["investment_cash_flow"] = dict(
        sorted(financials["investment_cash_flow"].items())
    )

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

    stream_message(f"Finding out how big is {name}'s backlog.", MessageType.info)

    backlog_finder = BacklogFinder()
    backlog = await backlog_finder.run(name, prompt_backlog)

    # Create a summary of the company
    prompt_summarizer = {
        "company": name,
        "latest_10k": reports["latest_10k"]["document"],
        "latest_10q": reports["latest_10q"]["document"]
    }

    stream_message(
        "Creating a summary based on the latest SEC filings.",
        MessageType.info
    )

    summarizer = Summarizer()
    summary = await summarizer.run(name, prompt_summarizer)

    financial_data = {
        "name": name,
        "ticker": ticker,
        "last_price": last_price,
        "revenue": financials["revenue"],
        "r_and_d_expense": financials["r_and_d_expense"],
        "operating_income": financials["operating_income"],
        "cash_and_equivalents": financials["cash_and_equivalents"],
        "marketable_securities": financials["marketable_securities"],
        "accounts_receivable": financials["accounts_receivable"],
        "total_assets": financials["total_assets"],
        "current_liabilities": financials["current_liabilities"],
        "long_term_debt": financials["long_term_debt"],
        "shareholders_equity": financials["shareholders_equity"],
        "investment_cash_flow": financials["investment_cash_flow"],
        "share_count": financials["share_count"],
        "backlog": backlog,
        "summary": summary,
        "historical_prices": price_history
    }

    stock = Stock(**financial_data)
    save_stock(stock, reports)
    stream_message("Saved stock to database.", MessageType.info)

    return stock
