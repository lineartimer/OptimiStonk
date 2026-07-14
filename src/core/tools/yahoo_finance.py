import asyncio
from datetime import date
import yfinance as yf


class Stonk:
    def __init__(self, ticker: str, price_series: list, time_series: list):
        self.ticker = ticker

        self._price_series = price_series
        self._time_series = time_series

    def get_price_day(self, year: int, month: int, day: int) -> float:
        """
            Returns the close price of the given day.
        """

        return self._get_last_price(lambda value: value == date(year, month, day))

    def get_price_week(self, year: int, week: int) -> float:
        """
            Returns the close price of the last day of the given week
            that the stock was traded on.
        """

        # Validate week
        date.fromisocalendar(year, week, 1)
        return self._get_last_price(
            lambda value: value.isocalendar()[:2] == (year, week)
        )

    def get_price_month(self, year: int, month: int) -> float:
        """
            Returns the close price of the last day of the given month
            that the stock was traded on.
        """

        # Validate month
        date(year, month, 1)
        return self._get_last_price(
            lambda value: (value.year, value.month) == (year, month)
        )
    
    def _get_last_price(self, matches) -> float:
        for price, timestamp in zip(
            reversed(self._price_series), reversed(self._time_series)
        ):
            if matches(timestamp):
                return float(price)

        raise ValueError(f"No price data found for {self.ticker} in that period")


async def get_stonk(ticker: str) -> Stonk:
    ticker = ticker.strip().upper()

    history = await asyncio.to_thread(
        yf.Ticker(ticker).history,
        period="max",
        auto_adjust=False,
        actions=False
    )

    prices = history["Close"].dropna()
    if prices.empty:
        raise ValueError(f"No data for {ticker}.")

    return Stonk(
        ticker,
        prices.tolist(),
        [timestamp.date() for timestamp in prices.index]
    )
