from datetime import datetime
from edgar import Company
from edgar.ttm.splits import detect_splits
import structlog


_logger = structlog.get_logger(__name__)


UNIT = 1_000_000


async def get_financial_info(ticker: str, years: int = 5) -> dict:
    """
        Download financial data of the given company from the EDGAR database.
    """

    _logger.info(f"Downloaded financial data for {ticker} "
                 "from the EDGAR database.")

    return {
        "annual": await _get_annual_data(ticker, years),
        "quarterly": await _get_quarterly_data(ticker, years)
    }


async def _get_annual_data(ticker: str, years: int) -> dict:
    company = Company(ticker)
    form_10ks = company.get_filings(form="10-K")
    splits = detect_splits(company.get_facts().get_all_facts())

    annual_revenues = {}
    share_counts = {}

    cnt = 0
    skip = False
    split = 1
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
        last_year = int(periods[1].end_date[:4])

        split_this_year = 1
        split_last_year = 1
        for s in splits:
            if s["date"].year == this_year:
                split_this_year *= s["ratio"]
            
            if s["date"].year == last_year:
                split_last_year *= s["ratio"]

        # This year
        split *= split_this_year

        annual_revenues[this_year] = int(income_statement["Revenue"].values[0] / UNIT)
        share_counts[this_year] = int(split * xbrl.facts.time_series("us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding").iloc[-1]["numeric_value"] / UNIT)

        # Last year
        annual_revenues[last_year] = int(income_statement["Revenue"].values[1] / UNIT)
        share_counts[last_year] = int(split * xbrl.facts.time_series("us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding").iloc[-2]["numeric_value"]  / UNIT)

        split *= split_last_year
        
        cnt += 1
        skip = True

        if 2 * cnt > years:
            if len(annual_revenues) > years:
                annual_revenues.popitem()
                share_counts.popitem()
            
            break

    return {
        "revenues": dict(sorted(annual_revenues.items())),
        "share_counts": dict(sorted(share_counts.items()))
    }


async def _get_quarterly_data(ticker: str, years: int) -> dict:
    company = Company(ticker)
    form_10qs = company.get_filings(form="10-Q")

    quarterly_revenues = {}
    quarterly_share_counts = {}

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
        quarterly_revenue = int(income_statement["Revenue"].values[0] / UNIT)
        quarterly_share_count = int(xbrl.facts.time_series("us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding").iloc[-1]["numeric_value"] / UNIT)

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
                missing_revenue = int(
                    (
                        list(quarterly_revenues.values())[-1] +
                        quarterly_revenue
                    ) / 2
                )
                quarterly_revenues[f"{year_of_missing_quarter}/{missing_quarter}"] = missing_revenue

                missing_share_count = int(
                    (
                        list(quarterly_share_counts.values())[-1] +
                        quarterly_share_count
                    ) / 2
                )
                quarterly_share_counts[f"{year_of_missing_quarter}/{missing_quarter}"] = missing_share_count
                
                missing_quarter = None

        quarterly_revenues[f"{year}/{quarter}"] = quarterly_revenue
        quarterly_share_counts[f"{year}/{quarter}"] = quarterly_share_count

        previous_quarter = quarter

    return {
        "revenues": dict(sorted(quarterly_revenues.items())),
        "share_counts": dict(sorted(quarterly_share_counts.items()))
    }