from datetime import datetime
from edgar import Company
from edgar.ttm.splits import detect_splits
import structlog


_logger = structlog.get_logger(__name__)


UNIT = 1_000_000


REVENUE_NAMES = {
    "us-gaap_Revenues",
    "us-gaap_SalesRevenueNet",
    "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax"
}


R_AND_D_NAMES = {
    "us-gaap_ResearchAndDevelopmentCosts",
    "us-gaap_ResearchAndDevelopmentExpense",
    "us-gaap_ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost"
}

SHARE_COUNT_NAMES = (
    "us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding",
    "us-gaap:WeightedAverageNumberOfShareOutstandingBasicAndDiluted",
    "us-gaap:WeightedAverageNumberOfSharesOutstandingBasic"
)


class EdgarTickerNotFoundError(Exception):
    pass


class EdgarParseError(Exception):
    pass


class EdgarDataLessThanTwoQuartersError(Exception):
    pass


class _CouldNotFindRevenueError(LookupError):
    pass


class _CouldNotFindShareCountError(LookupError):
    pass


async def get_stock_info(ticker: str, years: int = 5) -> dict:
    """
    Downloads financial data of a company from the EDGAR database.

    Args:
        ticker: Ticker symbol of the company.
        years: Time period of the financial data.
    """

    try:
        company = Company(ticker)

    except Exception as e:
        raise EdgarTickerNotFoundError(str(e))

    form_10qs = company.get_filings(form="10-Q", amendments=False)
    splits = detect_splits(company.get_facts().get_all_facts())

    quarterly_revenues = {}
    quarterly_r_and_d_expenses = {}
    quarterly_share_counts = {}
    quarterly_investments = {}

    previous_quarter = None
    missing_quarter = None
    split = 1
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

        try:
            quarterly_revenue = int(_get_revenue(income_statement) / UNIT)
            quarterly_r_and_d_expense = int(_get_r_and_d_expense(income_statement) / UNIT)
            quarterly_share_count = int(split * _get_weighted_average_share_count(xbrl) / UNIT)
            quarterly_investment = int(_get_investment_cashflow(xbrl) / UNIT)

        except LookupError as e:
            # Stop processing if financial data cannot be extracted from the current 10-Q
            _logger.warning("Stopped processing EDGAR data.", ticker=ticker, quarter=quarter, error=str(e))
            raise EdgarParseError(f"{str(e)} Affected quarter: {year}/{quarter}.")

        for s in splits:
            if s["date"].year == year and (s["date"].month - 1) // 3 + 1 == quarter:
                split *= s["ratio"]

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
                key = f"{year_of_missing_quarter}/{missing_quarter}"

                missing_revenue = int(
                    (
                        list(quarterly_revenues.values())[-1] +
                        quarterly_revenue
                    ) / 2
                )
                quarterly_revenues[key] = missing_revenue

                missing_r_and_d_expense = int(
                    (
                        list(quarterly_r_and_d_expenses.values())[-1] +
                        quarterly_r_and_d_expense
                    ) / 2
                )
                quarterly_r_and_d_expenses[key] = missing_r_and_d_expense

                missing_share_count = int(
                    (
                        list(quarterly_share_counts.values())[-1] +
                        quarterly_share_count
                    ) / 2
                )
                quarterly_share_counts[key] = missing_share_count

                missing_investment = int(
                    (
                        list(quarterly_investments.values())[-1] +
                        quarterly_investment
                    ) / 2
                )
                quarterly_investments[key] = missing_investment
                
                missing_quarter = None

        key = f"{year}/{quarter}"

        quarterly_revenues[key] = quarterly_revenue
        quarterly_r_and_d_expenses[key] = quarterly_r_and_d_expense
        quarterly_share_counts[key] = quarterly_share_count
        quarterly_investments[key] = quarterly_investment

        previous_quarter = quarter

    if len(quarterly_revenues) < 2:
        raise EdgarDataLessThanTwoQuartersError(f"Less than 2 quarters of financial data could be parsed from EDGAR for {ticker}.")

    if len(quarterly_revenues) > 4 * years:
        quarterly_revenues.popitem()
        quarterly_r_and_d_expenses.popitem()
        quarterly_share_counts.popitem()
        quarterly_investments.popitem()

    latest_10k = company.get_filings(form="10-K").latest(1) or ""
    latest_10q = form_10qs.latest(1) or ""

    _logger.info(f"Downloaded financial data for {company.name} "
                 "from the EDGAR database.")

    financials = {
        "revenue": dict(sorted(quarterly_revenues.items())),
        "r_and_d_expense": dict(sorted(quarterly_r_and_d_expenses.items())),
        "share_count": dict(sorted(quarterly_share_counts.items())),
        "investment_cash_flow": dict(sorted(quarterly_investments.items()))
    }

    reports = {
        "latest_10k": {
            "date": latest_10k.filing_date.isoformat() if latest_10k else "",
            "document": latest_10k.markdown() if latest_10k else ""
        },
        "latest_10q": {
            "date": latest_10q.filing_date.isoformat() if latest_10q else "",
            "document": latest_10q.markdown() if latest_10q else ""
        }
    }

    return financials, reports


def _get_revenue(income_statement) -> float:
    # Try to find revenues
    for row in income_statement.render().rows:
        concept = (row.metadata or {}).get("concept", "").replace(":", "_")

        if concept in REVENUE_NAMES:
            if row.cells and row.cells[0].value is not None:
                return row.cells[0].value

    # If nothing else works, try searching for it
    for label in ("total revenue", "revenue", "revenues"):
        for match in income_statement.search(label):
            if match.values and match.values[0] is not None:
                return match.values[0]
    
    raise _CouldNotFindRevenueError("Couldn't find revenue in income statement.")


def _get_r_and_d_expense(income_statement) -> float:
    # Try to find R&D expenses
    for row in income_statement.render().rows:
        concept = (row.metadata or {}).get("concept", "").replace(":", "_")
        if concept not in R_AND_D_NAMES:
            continue

        if row.cells and row.cells[0].value is not None:
            return row.cells[0].value

    # If nothing else works, try searching for it
    for match in income_statement.search("research and development"):
        if match.values and match.values[0] is not None:
            return match.values[0]

    # The company doesn't do R&D
    return 0


def _get_weighted_average_share_count(xbrl) -> float:
    # Try to find share count
    for concept in SHARE_COUNT_NAMES:
        df = xbrl.facts.time_series(concept)

        if not df.empty:
            values = df["numeric_value"].dropna()
            if not values.empty:
                return float(values.iloc[-1])

    raise _CouldNotFindShareCountError("Couldn't find share count.")


def _get_investment_cashflow(xbrl) -> float:
    # Try to find investment cashflow
    try:
        investment_df = xbrl.facts.time_series("us-gaap:NetCashProvidedByUsedInInvestingActivities")
        return investment_df.iloc[-1]["numeric_value"]

    except Exception as e:
        raise _CouldNotFindShareCountError("Couldn't find investment cachflow.")
