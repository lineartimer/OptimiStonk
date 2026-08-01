import structlog
import yfinance as yf


_logger = structlog.get_logger(__name__)


async def get_historical_prices(ticker: str, years: int) -> dict:
    """
        Download historical prices of the given stock from Yahoo Finance.
    """

    stock = yf.Ticker(ticker)

    price_history = stock.history(
        period=f"{years}y",
        interval="1d",
        auto_adjust=False,
        actions=True
    )

    info = stock.get_info()
    name = info["longName"]

    prices_by_quarter = {}
    previous_year = None
    previous_quarter = None
    close_price = None
    for dt, price in price_history.iterrows():
        if close_price:
            previous_close_price = close_price

        date = dt.date()
        year = date.year
        quarter = (date.month - 1) // 3 + 1

        close_price = round(price["Close"], 2)

        if not previous_year:
            previous_year = year

        if not previous_quarter:
            previous_quarter = quarter

        if year > previous_year or quarter > previous_quarter:
            # Start of a new quarter
            prices_by_quarter[f"{previous_year}/{previous_quarter}"] = previous_close_price

            previous_year = year
            previous_quarter = quarter
    
    _logger.info(f"Downloaded price data for {ticker} from Yahoo Finance.")

    return name, prices_by_quarter
