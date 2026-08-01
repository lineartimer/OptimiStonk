from datetime import datetime
from edgar import Company
import structlog


_logger = structlog.get_logger(__name__)


async def get_financial_info(ticker: str, years: int = 5) -> dict:
    """
        Download financial data of the given company from the EDGAR database.
    """

    _logger.info(f"Downloaded financial data for {ticker} "
                 "from the EDGAR database.")

    return {
        "annual_revenues": await _get_annual_revenues(ticker, years),
        "quarterly_revenues": await _get_quarterly_revenues(ticker, years)
    }


async def _get_annual_revenues(ticker: str, years: int) -> dict:
    company = Company(ticker)
    form_10ks = company.get_filings(form="10-K")

    cnt = 0
    skip = False
    annual_revenues = {}
    for form_10k in form_10ks:
        # Balance sheets contain data for the last two years,
        # so we can skip every other year
        if skip:
            skip = False
            continue

        xbrl = form_10k.xbrl()
        income_statement = xbrl.statements.income_statement()
        periods = income_statement.render().header.periods

        this_year = int(periods[0].end_date[:4])
        current_revenue = int(income_statement["Revenue"].values[0] / 1_000_000)
        annual_revenues[this_year] = current_revenue

        last_year = int(periods[1].end_date[:4])
        previous_revenue = int(income_statement["Revenue"].values[1] / 1_000_000)
        annual_revenues[last_year] = previous_revenue

        cnt += 1
        skip = True

        if 2 * cnt > years:
            if len(annual_revenues) > years:
                annual_revenues.popitem()
            
            break

    return dict(sorted(annual_revenues.items()))


async def _get_quarterly_revenues(ticker: str, years: int) -> dict:
    company = Company(ticker)
    form_10qs = company.get_filings(form="10-Q")

    quarterly_revenues = {}
    previous_quarter = None
    missing_quarter = None
    for form_10q in form_10qs:
        # As full-year quarters are not reported,
        # every year will have only 3 quarters
        xbrl = form_10q.xbrl()
        income_statement = xbrl.statements.income_statement()
        period = income_statement.render().header.periods[0]

        year = int(period.end_date[:4])
        if year < datetime.now().year - years:
            break

        quarter = (int(period.end_date[5:7]) - 1) // 3 + 1
        quarterly_revenue = int(income_statement["Revenue"].values[0] / 1_000_000)
        
        if previous_quarter:
            if previous_quarter - quarter == 2:
                # Cases:
                # - 2 is missing: 4 3 1  4 3 1
                # - 3 is missing: 4 2 1  4 2 1
                missing_quarter = quarter + 1
                year_of_missing_quarter = year
                
            elif quarter - previous_quarter == 2:
                # Cases:
                # - 1 is missing: 4 3 2  4 3 2
                # - 4 is missing: 3 2 1  3 2 1
                missing_quarter = 1 if quarter == 4 else 4
                year_of_missing_quarter = year + 1 if missing_quarter == 1 else year

            if missing_quarter:
                # Estimate missing quarter by the quarters surrounding it
                quarterly_revenues_list = list(quarterly_revenues.values())
                missing_revenue = (
                    quarterly_revenues_list[-1] +
                    quarterly_revenue
                ) / 2
                
                quarterly_revenues[f"{year_of_missing_quarter}/{missing_quarter}"] = missing_revenue

                missing_quarter = None

        quarterly_revenues[f"{year}/{quarter}"] = quarterly_revenue

        previous_quarter = quarter

    return dict(sorted(quarterly_revenues.items()))