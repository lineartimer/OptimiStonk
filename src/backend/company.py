import numpy as np


class Company:
    def __init__(self,
                 name: str,
                 ticker: str,
                 last_price: int,
                 historical_prices: dict,
                 revenue: dict,
                 r_and_d_expense: dict,
                 investment_cash_flow: dict,
                 share_count: dict,
                 backlog: int
    ):
        self.name = name
        self.ticker = ticker
        self.last_price = last_price

        self._historical_data = {}

        for quarter in revenue.keys():
            self._historical_data[quarter] = {
                "price": historical_prices[quarter],
                "revenue": revenue[quarter],
                "r_and_d_expense": r_and_d_expense[quarter],
                "investment_cash_flow": investment_cash_flow[quarter],
                "share_count": share_count[quarter]
            }

        self.backlog = backlog

    def get_price(self, quarter):
        return self._historical_data[quarter]["price"]

    def get_revenue(self, quarter):
        return self._historical_data[quarter]["revenue"]

    def get_r_and_d_expense(self, quarter):
        return self._historical_data[quarter]["r_and_d_expense"]

    def get_investment_cash_flow(self, quarter):
        return self._historical_data[quarter]["investment_cash_flow"]

    def get_share_count(self, quarter):
        return self._historical_data[quarter]["share_count"]

    def rank(self):
        # Can handle negative growth
        return round((1 + self.revenue_growth_per_year()) / self.price_to_backlog_ratio(), 2)

    def price_to_revenue_ratio(self):
        last_quarter = self._get_last_quarter()
        return round(self.last_price * self.get_share_count(last_quarter) / (4 * self.get_revenue(last_quarter)), 2)

    def price_to_backlog_ratio(self):
        last_quarter = self._get_last_quarter()
        return round(self.last_price * self.get_share_count(last_quarter) / self.backlog, 2)

    def revenue_growth_per_year(self):
        revenues = np.array(
            [
                data["revenue"]
                for data in self._historical_data.values()
            ],
            dtype=float
        )

        quarters = np.arange(revenues.size)
        quarterly_log_growth = np.polyfit(
            quarters,
            np.log(revenues),
            deg=1
        )[0]

        annual_growth = np.expm1(4 * quarterly_log_growth)

        return round(float(annual_growth), 2)

    def relative_hype(self):
        min = float("inf")
        max = float("-inf")
        for quarter in self._historical_data.keys():
            share_count = self.get_share_count(quarter)
            price = self.get_price(quarter)
            revenue = self.get_revenue(quarter)

            price_to_revenue = share_count * price / (4 * revenue)

            if price_to_revenue < min:
                min = price_to_revenue

            if price_to_revenue > max:
                max = price_to_revenue

        current = share_count * self.last_price / (4 * revenue)

        return round((current - min) / (max - min), 2)

    def to_json(self) -> dict:
        return {
            "name": self.name,
            "ticker": self.ticker,
            "last_price": self.last_price,
            "rank": self.rank(),
            "backlog": self.backlog,
            "financial_data": {
                quarter: {
                    "revenue": data["revenue"],
                    "r_and_d_expense": data["r_and_d_expense"],
                    "investment_cash_flow": data["investment_cash_flow"],
                    "share_count": data["share_count"]
                } for quarter, data in self._historical_data.items()
            },
            "historical_prices": {
                quarter: data["price"] for quarter, data in self._historical_data.items()
            },
            "metrics": {
                "price_to_revenue_ratio": self.price_to_revenue_ratio(),
                "price_to_backlog_ratio": self.price_to_backlog_ratio(),
                "revenue_growth_per_year": self.revenue_growth_per_year(),
                "relative_hype": self.relative_hype()
            },
        }

    def _get_last_quarter(self):
        return list(self._historical_data)[-1]