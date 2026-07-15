from edgar import Company
import os
import structlog


_logger = structlog.get_logger(__name__)


async def get_financial_info(ticker: str) -> dict:
    company = Company("AAPL")

    form_10Ks = company.get_filings(form="10-K")
    form_10Qs = company.get_filings(form="10-Q")
    