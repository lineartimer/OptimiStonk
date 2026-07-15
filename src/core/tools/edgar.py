from edgar import Company
import structlog


_logger = structlog.get_logger(__name__)


async def get_financial_info(ticker: str) -> dict:
    company = Company(ticker)

    form_10Ks = company.get_filings(form="10-K")
    form_10Qs = company.get_filings(form="10-Q")

    annual_revenues = []
    for form_10K in form_10Ks:
        xbrl = form_10K.xbrl()
        income = xbrl.statements.income_statement()
        annual_revenues.append(income.loc["Revenue", form_10K.filing_date.year])

    quarterly_revenues = []
    for form_10Q in form_10Qs:
        xbrl = form_10Q.xbrl()
        income = xbrl.statements.income_statement()
        annual_revenues.append(income.loc["Revenue", form_10Q.filing_date.year])

    return {
        "annual_revenues": annual_revenues,
        "quarterly_revenues": quarterly_revenues
    }