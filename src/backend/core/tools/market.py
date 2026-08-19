import csv
import io

from backend.core.tools.web import download_file


NASDAQ_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"

STOCK_TYPES = {
    "Common Stock",
    "Class A Ordinary Shares",
    "Ordinary Shares",
    "Class A Common Stock",
    "Common Shares",
}


async def download_stock_list() -> dict[str, dict]:
    """
    Downloads a list of tradable stocks.
    """

    file = await download_file(NASDAQ_LISTED_URL)
    rows = csv.DictReader(io.StringIO(file), delimiter="|")

    return {
        row["Symbol"]: _split_security_name(row["Security Name"])
        for row in rows
        if not row["Symbol"].startswith("File Creation Time") and _is_stock(row)
    }


def _split_security_name(security_name: str) -> dict:
    company_name, separator, stock_type = security_name.rpartition(" - ")
    if not separator:
        company_name = security_name
        stock_type = ""
    
    return {
        "company_name": company_name,
        "stock_type": stock_type
    }


def _is_stock(row: dict[str, str]) -> bool:
    security = _split_security_name(row["Security Name"])
    return security["stock_type"] in STOCK_TYPES
