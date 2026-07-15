from datetime import datetime
from edgar import Company
import structlog


_logger = structlog.get_logger(__name__)


async def get_financial_info(ticker: str, years: int = 5) -> dict:
    """
        Download financial data of the given company from the EDGAR database.
    """

    company = Company(ticker)

    form_10Ks = company.get_filings(form="10-K")
    form_10Qs = company.get_filings(form="10-Q")

    cnt = 0
    skip = False
    annual_revenues = []
    for form_10K in form_10Ks:
        # Balance sheets contain data for the last two years,
        # so we can skip every other year
        if skip:
            skip = False
            continue

        xbrl = form_10K.xbrl()
        income_statement = xbrl.statements.income_statement()
        periods = income_statement.render().header.periods
        
        annual_revenues.append({
            "year": int(periods[0].end_date[:4]),
            "revenue": income_statement["Revenue"].values[0]
        })
        annual_revenues.append({
            "year": int(periods[1].end_date[:4]),
            "revenue": income_statement["Revenue"].values[1]
        })

        cnt += 1
        skip = True

        if 2 * cnt > years:
            break

    quarterly_revenues = []
    for form_10Q in form_10Qs:
        xbrl = form_10Q.xbrl()
        income_statement = xbrl.statements.income_statement()
        period = income_statement.render().header.periods[0]

        year = int(period.end_date[:4])
        if year < datetime.now().year - years:
            break

        quarterly_revenues.append({
            "year": year,
            "quarter": (int(period.end_date[5:7]) - 1) // 3 + 1,
            "revenue": income_statement["Revenue"].values[0]
        })
    
    _logger.info(f"Downloaded financial data for {ticker} "
                 "from the EDGAR database.")

    return {
        "annual_revenues": annual_revenues[:years],
        "quarterly_revenues": quarterly_revenues
    }
