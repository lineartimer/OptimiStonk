import csv
from enum import Enum
import io
import re

from backend.core.tools.web import download_file


NASDAQ_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
NYSE_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"


_NYSE_SECURITY_DESCRIPTION = re.compile(
    r"\b(?:Class\s+\S+|Series\s+\S+|Common Stock|Common Shares|Ordinary Shares|"
    r"Preferred|Preference|Depositary|Depository|Warrants?|Rights?|Units?|"
    r"Notes?|Bonds?|Convertible|Redeemable|Non[- ]?Voting|Voting|Subordinate|Restricted)\b",
    re.IGNORECASE
)


class Exchange(str, Enum):
    nasdaq = "NASDAQ"
    nyse = "NYSE"


class StockType(str, Enum):
    common_stock = "Common Stock"
    class_a_ordinary_shares = "Class A Ordinary Shares"
    ordinary_shares = "Ordinary Shares"
    class_a_common_stock = "Class A Common Stock"
    common_shares = "Common Shares"


async def download_stock_list(exchange: Exchange) -> dict[str, dict]:
    """
    Downloads a list of tradable stocks.
    """

    if exchange == Exchange.nasdaq:
        url, symbol_field = NASDAQ_LISTED_URL, "Symbol"
    else:
        url, symbol_field = NYSE_LISTED_URL, "ACT Symbol"

    file = await download_file(url)
    rows = csv.DictReader(io.StringIO(file), delimiter="|")

    stocks = {}
    for row in rows:
        ticker = (row.get(symbol_field) or "").strip()
        if not ticker or ticker.startswith("File Creation Time"):
            continue

        if row.get("Test Issue") != "N" or row.get("ETF") != "N":
            continue
        
        if exchange == Exchange.nyse and row.get("Exchange") != "N":
            continue

        security = _split_security_name(row["Security Name"], exchange)

        try:
            security["stock_type"] = StockType(security["stock_type"]).value

        except ValueError:
            continue

        stocks.setdefault(ticker, {**security, "stock_exchange": exchange.value})

    return stocks


def _split_security_name(security_name: str, exchange: Exchange) -> dict:
    security_name = security_name.strip()
    name, separator, stock_type = security_name.rpartition(" - ")

    if not separator:
        name = security_name
        stock_type = ""

        if exchange == Exchange.nyse:
            description = _NYSE_SECURITY_DESCRIPTION.search(security_name)

            if description:
                name = security_name[:description.start()].strip()
                stock_type = security_name[description.start():]

    return {
        "name": name,
        "stock_type": stock_type
    }
