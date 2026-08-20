import structlog
import yfinance as yf


_logger = structlog.get_logger(__name__)


async def get_price_history(ticker: str, years: int) -> dict:
    """
    Downloads historical prices of a stock from Yahoo Finance.

    Args:
        ticker: Ticker symbol of the company.
        years: Time period of the prices.
    """

    stock = yf.Ticker(ticker)

    last_price = round(float(stock.fast_info.last_price), 2)

    price_history = stock.history(
        period=f"{years + 1}y",
        interval="1d",
        auto_adjust=False,
        actions=True
    )

    info = stock.get_info()
    name = info["longName"]

    prices_by_quarter = {}
    extra_price_point = {}

    close_price = None
    previous_year = None
    previous_quarter = None
    period_finished = False
    for dt, price in reversed(list(price_history.iterrows())):
        date = dt.date()
        year = date.year
        quarter = (date.month - 1) // 3 + 1
        close_price = round(price["Close"], 2)

        if not previous_year:
            previous_year = year

        if not previous_quarter:
            previous_quarter = quarter

        if year < previous_year or quarter < previous_quarter:
            # Start of a new quarter (iterating backward in time)
            if len(prices_by_quarter) < 4 * years:
                prices_by_quarter[f"{year}/{quarter}"] = close_price
            else:
                # Return one extra price point
                extra_price_point[f"{year}/{quarter}"] = close_price
                period_finished = True
                break

            previous_year = year
            previous_quarter = quarter

    if len(prices_by_quarter) > 0 and not period_finished:
        quarter, price = prices_by_quarter.popitem()
        extra_price_point[quarter] = price
    
    if len(prices_by_quarter) < 2:
        raise ValueError(f"Less than 2 quarters of financial data could be downloaded from Yahoo Finance for {ticker}.")

    _logger.info("Downloaded price data for from Yahoo Finance.", company=name)

    # Return prices in normal order
    return name, last_price, dict(reversed(prices_by_quarter.items())), extra_price_point
