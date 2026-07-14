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
        date.fromisocalendar(year, week, 1)  # Validate the ISO week.
        return self._get_last_price(
            lambda value: value.isocalendar()[:2] == (year, week)
        )

    def get_price_month(self, year: int, month: int) -> float:
        """
            Returns the close price of the last day of the given month
            that the stock was traded on.
        """
        date(year, month, 1)  # Validate the month.
        return self._get_last_price(
            lambda value: (value.year, value.month) == (year, month)
        )


async def get_stonk(ticker: str) -> Stonk:
    ticker = ticker.strip().upper()
    if not ticker:
        raise ValueError("Ticker cannot be empty")

    history = await asyncio.to_thread(
        yf.Ticker(ticker).history,
        period="max",
        auto_adjust=False,
        actions=False,
    )
    prices = history["Close"].dropna()
    if prices.empty:
        raise ValueError(f"No price data found for {ticker}")

    return Stonk(
        ticker,
        prices.tolist(),
        [timestamp.date() for timestamp in prices.index],
    )
