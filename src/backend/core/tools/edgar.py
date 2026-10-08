import asyncio
from datetime import datetime
from enum import Enum
from edgar import Company, XBRL
from edgar.ttm.splits import detect_splits
from edgar.xbrl.statements import Statement
from itertools import product
import json
from pathlib import Path
import re
import structlog

from backend.api.helpers.streamer import stream_message
from backend.core.utils.logger import log_and_stream
from backend.core.utils.message_type import MessageType


UNIT = 1_000_000

with Path(__file__).with_name("edgar.json").open(encoding="utf-8") as f:
    edgar_config = json.load(f)

    _document_internals = edgar_config["document_internals"]
    _fields = edgar_config["fields"]


_logger = structlog.get_logger(__name__)


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

    quarterly_data = {}
    for field_name in _fields:
        quarterly_data[field_name] = {
            "current_quarter": None,
            "all_quarters": {}
        }

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

            invalid_quarter = False
            for field_name in _fields:
                if _fields[field_name]["optional"]:
                    func = _get_optional_financial_data
                else:
                    func = _get_financial_data

                raw_value = func(xbrl, field_name)
                value = round(raw_value / UNIT)

                if field_name == "revenue":
                    # In some rare, esoteric cases, revenue can be negative
                    if value < 0:
                        _logger.warning("Negative revenue found.",
                            ticker=ticker,
                            quarter=f"{year}/{quarter}"
                        )

                        # We need to break out of the outer loop
                        invalid_quarter = True
                        break

                # Many companies don't report operating income.
                # Use net income as substitute in those cases
                if field_name == "net_income":
                    quarterly_data["operating_income"]["current_quarter"] = (
                        value
                        if quarterly_data["operating_income"]["current_quarter"] == 0
                        else quarterly_data["operating_income"]["current_quarter"]
                    )

                if field_name == "eps":
                    value = raw_value / split

                if field_name == "share_count":
                    value = round(
                        split * raw_value / UNIT
                    )
                
                quarterly_data[field_name]["current_quarter"] = value
            
            if invalid_quarter:
                break

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

                for field_name in quarterly_data:
                    missing_data = (
                        list(
                            quarterly_data[field_name]["all_quarters"].values()
                        )[-1] + quarterly_data[field_name]["current_quarter"]
                    ) / 2

                    if field_name != "eps":
                        missing_data = round(missing_data)
                    
                    quarterly_data[field_name]["all_quarters"][key] = (
                        missing_data
                    )
                
                missing_quarter = None

        key = f"{year}/{quarter}"
        for field_name in quarterly_data:
            quarterly_data[field_name]["all_quarters"][key] = (
                quarterly_data[field_name]["current_quarter"]
            )

        stream_message(".", new_line=False)
        previous_quarter = quarter

    while len(quarterly_data["revenue"]["all_quarters"]) > 4 * years:
        for field_name in quarterly_data:
            quarterly_data[field_name]["all_quarters"].popitem()

    form_10ks = company.get_filings(form="10-K")
    if (form_10ks.empty or
        len(quarterly_data["revenue"]["all_quarters"]) < 2
    ):
        raise EdgarParseError(
            f"Either a 10-K or at least 2 quarters of financial data "
            f"could not be found for {company.name}"
        )
    
    latest_10k = "" if form_10ks.empty else form_10ks.latest(1)
    latest_10q = "" if form_10qs.empty else form_10qs.latest(1)
    
    financials = {}
    for field_name in quarterly_data:
        financials[field_name] = _clean_result(
            quarterly_data[field_name]["all_quarters"]
        )

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

    tags = _document_internals[name]["tags"]
    labels = _generate_all_labels(
        _document_internals[name]["labels"]
    )

    financial_statement = _get_financial_statement(xbrl, statement_type)
    if not financial_statement:
        return None

    value = None
    for row in financial_statement.render().rows:
        tag = (row.metadata or {}).get("concept", "").replace(":", "_")

        if (
            tag.lower() in [t.lower() for t in tags] and
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
                    # but the value cannot be converted to a number (e.g. "").
                    # This means that the value is 0
                    if value is None:
                        value = 0.0

    return value


def _generate_all_labels(labels: dict) -> list[str]:
    variations = labels["variations"]
    result = []

    for pattern in labels["pattern"]:
        names = list(dict.fromkeys(re.findall(r"<([^>]+)>", pattern)))
        choices = [variations[name] for name in names]

        for values in product(*choices):
            label = pattern
            for name, value in zip(names, values):
                label = label.replace(f"<{name}>", value)
            
            result.append(label)

    return list(dict.fromkeys(result))


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
