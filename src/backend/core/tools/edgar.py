from collections.abc import Collection
from datetime import datetime
from edgar import Company, XBRL
from edgar.ttm.splits import detect_splits
from edgar.xbrl.statements import Statement
import structlog


_logger = structlog.get_logger(__name__)


UNIT = 1_000_000

QUARTER_NAMES = {"Q1", "Q2", "Q3", "Q4"}

# Revenues
REVENUE_CONCEPT_NAMES = {
    "us-gaap_Revenues",
    "us-gaap_SalesRevenueNet",
    "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax"
}

REVENUE_LABELS = {
    "Revenue",
    "Revenues",
    "Total revenue",
    "Net revenues"
}

# R&D expenses
R_AND_D_CONCEPT_NAMES = {
    "us-gaap_ResearchAndDevelopmentCosts",
    "us-gaap_ResearchAndDevelopmentExpense",
    "us-gaap_ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost"
}

R_AND_D_LABELS = {
    "Research and development"
}

# Number of shares outstanding assuming dilution
SHARE_COUNT_CONCEPT_NAMES = {
    "us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding"
}

SHARE_COUNT_LABELS = {
    "Diluted (in shares)"
}

# Investment cash flow
INVESTMENT_CASH_FLOW_CONCEPT_NAMES = {
    "us-gaap:NetCashProvidedByUsedInInvestingActivities"
}

INVESTMENT_CASH_FLOW_LABELS = {
    "Net cash provided by investing activities",
    "Net cash provided by (used in) investing activities",
    "Net cash used in investing activities"
}


class EdgarTickerNotFoundError(Exception):
    pass


class EdgarParseError(Exception):
    pass


class _CouldNotFindPeriodError(LookupError):
    pass


class _CouldNotFindRevenueError(LookupError):
    pass


class _CouldNotFindShareCountError(LookupError):
    pass


async def get_financial_data(ticker: str, years: int = 5) -> dict:
    """
    Downloads financial data of a company from the EDGAR database.

    Args:
        ticker: Ticker symbol of the company.
        years: Time period of the financial data.
    """

    try:
        company = Company(ticker)

    except Exception as e:
        raise EdgarTickerNotFoundError(f"Ticker not found. {str(e)}")

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
        try:
            # As full-year quarters are not reported, every year will have only 3 quarters
            xbrl, year, quarter = _get_xbrl_and_period(form_10q)

            if year < datetime.now().year - years:
                break

            quarterly_revenue = round(_get_revenue(xbrl) / UNIT)
            quarterly_r_and_d_expense = round(_get_r_and_d_expense(xbrl) / UNIT)
            quarterly_share_count = round(split * _get_weighted_average_share_count(xbrl) / UNIT)
            quarterly_investment = round(_get_investment_cashflow(xbrl) / UNIT)

        except LookupError as e:
            # Stop processing if financial data cannot be extracted from the current 10-Q
            _logger.warning("Stopped processing EDGAR data.", ticker=ticker, quarter=quarter, error=str(e))
            break

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

                missing_revenue = round(
                    (
                        list(quarterly_revenues.values())[-1] +
                        quarterly_revenue
                    ) / 2
                )
                quarterly_revenues[key] = missing_revenue

                missing_r_and_d_expense = round(
                    (
                        list(quarterly_r_and_d_expenses.values())[-1] +
                        quarterly_r_and_d_expense
                    ) / 2
                )
                quarterly_r_and_d_expenses[key] = missing_r_and_d_expense

                missing_share_count = round(
                    (
                        list(quarterly_share_counts.values())[-1] +
                        quarterly_share_count
                    ) / 2
                )
                quarterly_share_counts[key] = missing_share_count

                missing_investment = round(
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

    while len(quarterly_revenues) > 4 * years:
        quarterly_revenues.popitem()
        quarterly_r_and_d_expenses.popitem()
        quarterly_share_counts.popitem()
        quarterly_investments.popitem()

    form_10ks = company.get_filings(form="10-K")
    if form_10ks.empty and len(quarterly_revenues) < 2:
        raise EdgarParseError("Neither a 10-K nor at least 2 quarters of financial data has been found.")
    
    latest_10k = "" if form_10ks.empty else form_10ks.latest(1)
    latest_10q = "" if form_10qs.empty else form_10qs.latest(1)

    _logger.info(f"Downloaded financial data for {company.name} "
                 "from the EDGAR database.")

    financials = {
        "revenue": _clean_result(quarterly_revenues),
        "r_and_d_expense": _clean_result(quarterly_r_and_d_expenses),
        "share_count": _clean_result(quarterly_share_counts),
        "investment_cash_flow": _clean_result(quarterly_investments)
    }

    reports = {
        "latest_10k": {
            "date": latest_10k.filing_date.isoformat(),
            "document": latest_10k.markdown()
        } if latest_10k else {},
        "latest_10q": {
            "date": latest_10q.filing_date.isoformat(),
            "document": latest_10q.markdown()
        } if latest_10q else {}
    }

    return financials, reports


def _get_xbrl_and_period(form_10q) -> tuple[XBRL, int, int]:
    xbrl = form_10q.xbrl()
    income_statement = xbrl.statements.income_statement()
    rendered_income_statement = income_statement.render()

    period = None
    if rendered_income_statement.header.periods:
        period = rendered_income_statement.header.periods[0].end_date
    else:
        period_of_report = getattr(form_10q, "period_of_report", None)
        if period_of_report:
            period = str(period_of_report)[:10]

    if not period:
        raise _CouldNotFindPeriodError("Couldn't find period in 10-Q.")

    try:
        year = int(period[:4])
        quarter = (int(period[5:7]) - 1) // 3 + 1

    except:
        raise EdgarParseError("Error parsing quarter of 10-Q.", period=period)

    return xbrl, year, quarter


def _get_revenue(xbrl) -> float:
    income_statement = xbrl.statements.income_statement()

    # Try to find revenues in rendered income statement
    value = _parse_from_income_statement(income_statement, REVENUE_CONCEPT_NAMES)
    if value:
        return value

    # Try to find revenues in xbrl facts
    value = _parse_from_xbrl(xbrl, REVENUE_CONCEPT_NAMES, REVENUE_LABELS)
    if value:
        return value
    
    # If nothing else works, try searching for it
    for label in (REVENUE_LABELS):
        for match in income_statement.search(label):
            if match.values and match.values[0] is not None:
                return match.values[0]
    
    raise _CouldNotFindRevenueError("Couldn't find revenue in income statement.")


def _get_r_and_d_expense(xbrl) -> float:
    income_statement = xbrl.statements.income_statement()

    # Try to find R&D expenses in rendered income statement
    value = _parse_from_income_statement(income_statement, R_AND_D_CONCEPT_NAMES)
    if value:
        return value

    # Try to find R&D expenses in xbrl facts
    value = _parse_from_xbrl(xbrl, R_AND_D_CONCEPT_NAMES, R_AND_D_LABELS)
    if value:
        return value

    # If nothing else works, try searching for it
    for label in R_AND_D_LABELS:
        for match in income_statement.search(label):
            if match.values and match.values[0] is not None:
                return match.values[0]

    # The company doesn't do R&D
    return 0


def _get_weighted_average_share_count(xbrl) -> float:
    # Try to find share count in xbrl facts
    value = _parse_from_xbrl(xbrl, SHARE_COUNT_CONCEPT_NAMES, SHARE_COUNT_LABELS)
    if value:
        return value

    raise _CouldNotFindShareCountError("Couldn't find share count.")


def _get_investment_cashflow(xbrl) -> float:
    # Try to find share count in xbrl facts
    value = _parse_from_xbrl(xbrl, INVESTMENT_CASH_FLOW_CONCEPT_NAMES, INVESTMENT_CASH_FLOW_LABELS, True)
    if value:
        return value

    raise _CouldNotFindShareCountError("Couldn't find investment cachflow.")


def _parse_from_income_statement(income_statement: Statement, concepts: Collection[str]) -> float | None:
    for row in income_statement.render().rows:
        concept = (row.metadata or {}).get("concept", "").replace(":", "_")

        if concept in concepts:
            if row.cells and row.cells[0].value is not None:
                return row.cells[0].value

    return None


def _parse_from_xbrl(xbrl: XBRL, concepts: Statement, labels: Collection[str], allow_ytd: bool = False) -> float | None:
    for concept in concepts:
        df = xbrl.facts.time_series(concept)
        if df.empty:
            continue

        df = df.sort_values(by="date")
        for label in labels:
            filtered_df = df.loc[df["label"].eq(label)]
            if not allow_ytd:
                filtered_df = filtered_df.loc[filtered_df["fiscal_period"].isin(QUARTER_NAMES)]
            
            filtered_df = filtered_df["numeric_value"].dropna()
            if not filtered_df.empty:
                return float(filtered_df.iloc[-1])

    return None


def _clean_result(data: dict) -> dict:
    sorted_backward = dict(sorted(data.items(), reverse = True))

    result = {}
    q_frac_prev = None
    for q in sorted_backward.keys():
        year, quarter = q.split("/")
        q_frac = int(year) + int(quarter) / 4

        if q_frac_prev and q_frac_prev - q_frac > 0.25:
            break

        result[q] = sorted_backward[q]
        q_frac_prev = q_frac

    return dict(sorted(result.items()))