class Stonk:
    def __init__(self, ticker: str, price_series: list, time_series: list):
        self.ticker = ticker

        self._price_series = price_series
        self._time_series = time_series

    def get_price_day(self, year: int, month: int, day: int) -> float:
        """
            Returns the close price of the given day.
        """
        pass

    def get_price_week(self, year: int, week: int) -> float:
        """
            Returns the close price of the last day of the given week
            that the stock was traded on.
        """
        pass

    def get_price_month(self, year: int, month: int) -> float:
        """
            Returns the close price of the last day of the given month
            that the stock was traded on.
        """
        pass


async def get_stonk(ticker: str) -> Stonk:
    pass