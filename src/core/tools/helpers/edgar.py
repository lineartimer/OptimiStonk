from datetime import datetime
from edgar import Company
from edgar.ttm.splits import detect_splits
import structlog


_logger = structlog.get_logger(__name__)


UNIT = 1_000_000


R_AND_D_NAMES = {
    "us-gaap_ResearchAndDevelopmentCosts",
    "us-gaap_ResearchAndDevelopmentExpense",
    "us-gaap_ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost"
}


async def get_financial_info(ticker: str, years: int = 5) -> dict:
    """
        Download financial data of the given company from the EDGAR database.
    """

    company = Company(ticker)
    form_10qs = company.get_filings(form="10-Q")
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

        quarterly_revenue = int(income_statement["Revenue"].values[0] / UNIT)
        quarterly_r_and_d_expense = int(_get_r_and_d_expense(income_statement) / UNIT)
        quarterly_share_count = int(split * xbrl.facts.time_series("us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding").iloc[-1]["numeric_value"] / UNIT)

        investment_df = xbrl.facts.time_series("us-gaap:NetCashProvidedByUsedInInvestingActivities")

        quarterly_investment = int(investment_df.iloc[-1]["numeric_value"] / UNIT)

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

    quarterly_revenues.popitem()
    quarterly_r_and_d_expenses.popitem()
    quarterly_share_counts.popitem()
    quarterly_investments.popitem()

    _logger.info(f"Downloaded financial data for {ticker} "
                 "from the EDGAR database.")

    return {
        "revenue": dict(sorted(quarterly_revenues.items())),
        "r_and_d_expense": dict(sorted(quarterly_r_and_d_expenses.items())),
        "share_count": dict(sorted(quarterly_share_counts.items())),
        "investment_cash_flow": dict(sorted(quarterly_investments.items()))
    }


def _get_r_and_d_expense(income_statement) -> float:
    rendered_statement = income_statement.render()

    # Statement labels are chosen by each filer, so identify R&D by its
    # underlying XBRL concept rather than a particular display label
    for row in rendered_statement.rows:
        concept = (row.metadata or {}).get("concept", "").replace(":", "_")
        if concept not in R_AND_D_NAMES:
            continue

        if row.cells and row.cells[0].value is not None:
            return row.cells[0].value

    # If company-specific extension concepts cannot be enumerated in advance,
    # falling back to matching their rendered statement labels
    for match in income_statement.search("research and development"):
        if match.values and match.values[0] is not None:
            return match.values[0]

    raise ValueError(
        "The filing does not report a research and development expense."
    )