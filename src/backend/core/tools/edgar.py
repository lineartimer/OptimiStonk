import asyncio
import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from edgar import Company, XBRL
from edgar.ttm.splits import detect_splits
from edgar.xbrl.statements import Statement
import structlog

from backend.api.helpers.streamer import stream_message
from backend.core.utils.logger import log_and_stream
from backend.core.utils.message_type import MessageType


_logger = structlog.get_logger(__name__)


UNIT = 1_000_000

with Path(__file__).with_suffix(".json").open(encoding="utf-8") as f:
    _edgar_definitions = json.load(f)


class FinancialStatementType(str, Enum):
    income_statement = "IncomeStatement"
    balance_sheet = "BalanceSheet"
    cash_flow = "CashFlowStatement"


class EdgarTickerNotFoundError(Exception):
    pass


class EdgarParseError(Exception):
    pass


class _FinancialStatementNotFoundError(LookupError):
    pass


class _CouldNotFindPeriodError(LookupError):
    pass


class _CouldNotFindFinancialDataError(LookupError):
    pass


async def get_financial_data(ticker: str, years: int = 5) -> dict:
    """
    Downloads financial data of a company from the EDGAR database.

    Args:
        ticker: Ticker symbol of the company.
        years: Time period of the financial data.
    """

    return await asyncio.to_thread(_get_financial_data_impl, ticker, years)


def _get_financial_data_impl(ticker: str, years: int):
    stream_message("Downloading data from EDGAR", MessageType.info)

    try:
        company = Company(ticker)

    except Exception as e:
        raise EdgarTickerNotFoundError(f"Ticker not found. {str(e)}")

    form_10qs = company.get_filings(form="10-Q", amendments=False)
    splits = detect_splits(company.get_facts().get_all_facts())

    quarterly_revenues = {}
    quarterly_r_and_d_expenses = {}
    quarterly_operating_incomes = {}
    quarterly_net_incomes = {}
    quarterly_eps = {}
    quarterly_cash_and_equivalents = {}
    quarterly_marketable_securities = {}
    quarterly_accounts_receivable = {}
    quarterly_total_assets = {}
    quarterly_current_liabilities = {}
    quarterly_long_term_debts = {}
    quarterly_shareholders_equities = {}
    quarterly_share_counts = {}
    quarterly_investments = {}

    previous_quarter = None
    missing_quarter = None
    split = 1
    for form_10q in form_10qs:
        year = quarter = None
        
        try:
            # As full-year quarters are not reported,
            # every year will have only 3 quarters
            xbrl, year, quarter = _get_xbrl_and_period(form_10q)

            if year < datetime.now().year - years:
                break

            revenue = round(
                _get_optional_financial_data(xbrl, "revenue") / UNIT
            )

            # In some rare, esoteric cases, revenue can be negative
            if revenue < 0:
                _logger.warning("Negative revenue found.",
                    ticker=ticker,
                    quarter=f"{year}/{quarter}"
                )
                break

            r_and_d_expense = round(
                _get_optional_financial_data(xbrl, "r_and_d_expense") / UNIT
            )

            operating_income = round(
                _get_optional_financial_data(xbrl, "operating_income") / UNIT
            )

            net_income = round(
                _get_financial_data(xbrl, "net_income") / UNIT
            )

            eps = _get_financial_data(xbrl, "eps") / split

            cash_and_equivalents = round(
                _get_financial_data(xbrl, "cash_and_equivalents") / UNIT
            )

            marketable_securities = round(
                _get_optional_financial_data(xbrl, "marketable_securities") / UNIT
            )

            accounts_receivable = round(
                _get_optional_financial_data(xbrl, "accounts_receivable") / UNIT
            )

            total_assets = round(
                _get_financial_data(xbrl, "total_assets") / UNIT
            )

            current_liabilities = round(
                _get_financial_data(xbrl, "current_liabilities") / UNIT
            )

            long_term_debt = round(
                _get_optional_financial_data(xbrl, "long_term_debt") / UNIT
            )

            shareholders_equity = round(
                _get_financial_data(xbrl, "shareholders_equity") / UNIT
            )

            investment_cash_flow = round(
                _get_optional_financial_data(xbrl, "investment_cash_flow") / UNIT
            )

            share_count = round(
                split * _get_financial_data(xbrl, "share_count") / UNIT
            )

        except (LookupError, KeyError) as e:
            # Stop processing if financial data cannot be extracted from the current 10-Q
            log_and_stream("Stopped processing EDGAR data because of a parsing error.",
                MessageType.warning,
                ticker=ticker,
                quarter=f"{year}/{quarter}",
                error=str(e)
            )
            break

        except Exception as e:
            log_and_stream("Stopped processing EDGAR data.",
                MessageType.warning,
                ticker=ticker,
                quarter=f"{year}/{quarter}",
                error=str(e)
            )
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
                        revenue
                    ) / 2
                )
                quarterly_revenues[key] = missing_revenue

                missing_r_and_d_expense = round(
                    (
                        list(quarterly_r_and_d_expenses.values())[-1] +
                        r_and_d_expense
                    ) / 2
                )
                quarterly_r_and_d_expenses[key] = missing_r_and_d_expense

                missing_operating_income = round(
                    (
                        list(quarterly_operating_incomes.values())[-1] +
                        operating_income
                    ) / 2
                )
                quarterly_operating_incomes[key] = missing_operating_income

                missing_net_income = round(
                    (
                        list(quarterly_net_incomes.values())[-1] +
                        net_income
                    ) / 2
                )
                quarterly_net_incomes[key] = missing_net_income

                missing_eps = (
                    list(quarterly_eps.values())[-1] + eps
                ) / 2
                quarterly_eps[key] = missing_eps

                missing_cash_and_equivalents = round(
                    (
                        list(quarterly_cash_and_equivalents.values())[-1] +
                        cash_and_equivalents
                    ) / 2
                )
                quarterly_cash_and_equivalents[key] = missing_cash_and_equivalents

                missing_marketable_securities = round(
                    (
                        list(quarterly_marketable_securities.values())[-1] +
                        marketable_securities
                    ) / 2
                )
                quarterly_marketable_securities[key] = missing_marketable_securities

                missing_accounts_receivable = round(
                    (
                        list(quarterly_accounts_receivable.values())[-1] +
                        accounts_receivable
                    ) / 2
                )
                quarterly_accounts_receivable[key] = missing_accounts_receivable

                missing_total_assets = round(
                    (
                        list(quarterly_total_assets.values())[-1] +
                        total_assets
                    ) / 2
                )
                quarterly_total_assets[key] = missing_total_assets

                missing_current_liabilities = round(
                    (
                        list(quarterly_current_liabilities.values())[-1] +
                        current_liabilities
                    ) / 2
                )
                quarterly_current_liabilities[key] = missing_current_liabilities

                missing_long_term_debt = round(
                    (
                        list(quarterly_long_term_debts.values())[-1] +
                        long_term_debt
                    ) / 2
                )
                quarterly_long_term_debts[key] = missing_long_term_debt

                missing_shareholders_equity = round(
                    (
                        list(quarterly_shareholders_equities.values())[-1] +
                        shareholders_equity
                    ) / 2
                )
                quarterly_shareholders_equities[key] = missing_shareholders_equity

                missing_share_count = round(
                    (
                        list(quarterly_share_counts.values())[-1] +
                        share_count
                    ) / 2
                )
                quarterly_share_counts[key] = missing_share_count

                missing_investment = round(
                    (
                        list(quarterly_investments.values())[-1] +
                        investment_cash_flow
                    ) / 2
                )
                quarterly_investments[key] = missing_investment
                
                missing_quarter = None

        key = f"{year}/{quarter}"

        quarterly_revenues[key] = revenue
        quarterly_r_and_d_expenses[key] = r_and_d_expense
        quarterly_operating_incomes[key] = operating_income
        quarterly_net_incomes[key] = net_income
        quarterly_eps[key] = eps
        quarterly_cash_and_equivalents[key] = cash_and_equivalents
        quarterly_marketable_securities[key] = marketable_securities
        quarterly_accounts_receivable[key] = accounts_receivable
        quarterly_total_assets[key] = total_assets
        quarterly_current_liabilities[key] = current_liabilities
        quarterly_long_term_debts[key] = long_term_debt
        quarterly_shareholders_equities[key] = shareholders_equity
        quarterly_share_counts[key] = share_count
        quarterly_investments[key] = investment_cash_flow

        stream_message(".", new_line=False)
        previous_quarter = quarter

    while len(quarterly_revenues) > 4 * years:
        quarterly_revenues.popitem()
        quarterly_r_and_d_expenses.popitem()
        quarterly_operating_incomes.popitem()
        quarterly_net_incomes.popitem()
        quarterly_eps.popitem()
        quarterly_cash_and_equivalents.popitem()
        quarterly_marketable_securities.popitem()
        quarterly_accounts_receivable.popitem()
        quarterly_total_assets.popitem()
        quarterly_current_liabilities.popitem()
        quarterly_long_term_debts.popitem()
        quarterly_shareholders_equities.popitem()
        quarterly_share_counts.popitem()
        quarterly_investments.popitem()

    form_10ks = company.get_filings(form="10-K")
    if form_10ks.empty or len(quarterly_revenues) < 2:
        raise EdgarParseError(
            f"Either a 10-K or at least 2 quarters of financial data "
            f"could not be found for {company.name}"
        )
    
    latest_10k = "" if form_10ks.empty else form_10ks.latest(1)
    latest_10q = "" if form_10qs.empty else form_10qs.latest(1)

    financials = {
        "revenue": _clean_result(quarterly_revenues),
        "r_and_d_expense": _clean_result(quarterly_r_and_d_expenses),
        "operating_income": _clean_result(quarterly_operating_incomes),
        "net_income": _clean_result(quarterly_net_incomes),
        "eps": _clean_result(quarterly_eps),
        "cash_and_equivalents": _clean_result(quarterly_cash_and_equivalents),
        "marketable_securities": _clean_result(quarterly_marketable_securities),
        "accounts_receivable": _clean_result(quarterly_accounts_receivable),
        "total_assets": _clean_result(quarterly_total_assets),
        "current_liabilities": _clean_result(quarterly_current_liabilities),
        "long_term_debt": _clean_result(quarterly_long_term_debts),
        "shareholders_equity": _clean_result(quarterly_shareholders_equities),
        "share_count": _clean_result(quarterly_share_counts),
        "investment_cash_flow": _clean_result(quarterly_investments)
    }

    stream_message(".", new_line=False)

    try:
        reports = {
            "latest_10k": {
                "date": latest_10k.filing_date.isoformat(),
                "document": latest_10k.document.markdown()
            } if latest_10k else {},
            "latest_10q": {
                "date": latest_10q.filing_date.isoformat(),
                "document": latest_10q.document.markdown()
            } if latest_10q else {}
        }

    except Exception as e:
        raise EdgarParseError(
            f"Couldn't markdownify latest 10-K or 10-Q for {company.name}"
        )

    log_and_stream(
        f"Downloaded financial data from the EDGAR database.",
        MessageType.info
    )

    return financials, reports


def _get_financial_statement(
    xbrl: XBRL,
    statement_type: FinancialStatementType
) -> Statement | None:

    statements = xbrl.statements
    get_statement = {
        FinancialStatementType.income_statement: statements.income_statement,
        FinancialStatementType.balance_sheet: statements.balance_sheet,
        FinancialStatementType.cash_flow: statements.cash_flow_statement
    }[statement_type]

    financial_statement = get_statement()
    if financial_statement:
        return financial_statement

    # If the accessor returns None (can happen),
    # look up the financial statement in another way
    for statement in xbrl.get_all_statements():
        if statement.get("type") == statement_type.value:
            return statements[statement["role"]]

    return None


def _get_xbrl_and_period(form_10q) -> tuple[XBRL, int, int]:
    xbrl = form_10q.xbrl()
    income_statement = _get_financial_statement(
        xbrl, FinancialStatementType.income_statement
    )
    if not income_statement:
        raise _FinancialStatementNotFoundError(
            "Couldn't find income statement when parsing period."
        )

    rendered_income_statement = income_statement.render()

    period = None
    if rendered_income_statement.header.periods:
        period = rendered_income_statement.header.periods[0].end_date
    else:
        period_of_report = getattr(form_10q, "period_of_report", None)
        if period_of_report:
            period = str(period_of_report)[:10]

    if not period:
        raise _CouldNotFindPeriodError(f"Couldn't find {period} period in 10-Q.")

    try:
        year = int(period[:4])
        quarter = (int(period[5:7]) - 1) // 3 + 1

    except:
        raise EdgarParseError(f"Error parsing quarter {period} of 10-Q.")

    return xbrl, year, quarter


def _get_financial_data(xbrl:XBRL, name: str) -> float:
    value = _parse_value(xbrl, name)
    if value is not None:
        return value

    # If we can't find what we're looking for, it's an error
    raise _CouldNotFindFinancialDataError(f"Couldn't find {name}.")


def _get_optional_financial_data(xbrl: XBRL, name: str) -> float:
    value = _parse_value(xbrl, name)

    # If we can't find what we're looking for, it's zero
    return value if value is not None else 0


def _parse_value(xbrl: XBRL, name: str) -> float | None:
    # Try to find the value in the income statement, balance sheet, and cash flow
    value = _parse_from_financial_statement(xbrl, name, FinancialStatementType.income_statement)

    if value is None:
        value = _parse_from_financial_statement(xbrl, name, FinancialStatementType.balance_sheet)

    if value is None:
        value = _parse_from_financial_statement(xbrl, name, FinancialStatementType.cash_flow)

    return value


def _parse_from_financial_statement(
    xbrl: XBRL,
    name: str,
    statement_type: FinancialStatementType
) -> float | None:

    definitions = _edgar_definitions[name]
    concept_names = definitions["concept_names"]
    labels = definitions["labels"]

    financial_statement = _get_financial_statement(xbrl, statement_type)
    if not financial_statement:
        return None

    value = None
    for row in financial_statement.render().rows:
        concept = (row.metadata or {}).get("concept", "").replace(":", "_")

        if (
            concept.lower() in [concept.lower() for concept in concept_names] and
            _row_starts_with_label(row.label, labels)
        ):
            if row.cells and row.cells[0]:
                try:
                    parsed_value = float(row.cells[0].value)

                    # Accumulate all matching rows
                    # (Needed for parsing long term debt)
                    if value is None:
                        value = parsed_value
                    else:
                        value += parsed_value
                
                except:
                    # We have found the row in the financial statement
                    # but the value can't be converted to a number (e.g. "").
                    # This means that the value is 0
                    if value is None:
                        value = 0.0

    return value


def _row_starts_with_label(row_label: str, labels: list[str]) -> bool:
    row_label_lower_case = row_label.lower()
    return any(
        row_label_lower_case.startswith(label.lower()) for label in labels
    )


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
