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
        if (
            len(historical_prices) < 2 or
            len(revenue) < 2 or
            len(r_and_d_expense) < 2 or
            len(investment_cash_flow) < 2 or
            len(share_count) < 2
        ):
            raise ValueError("At least two quarters of financial data needed.")

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

    def get_price(self, quarter: str) -> int:
        return self._historical_data[quarter]["price"]

    def get_revenue(self, quarter: str) -> int:
        return self._historical_data[quarter]["revenue"]

    def get_r_and_d_expense(self, quarter: str) -> int:
        return self._historical_data[quarter]["r_and_d_expense"]

    def get_investment_cash_flow(self, quarter: str) -> int:
        return self._historical_data[quarter]["investment_cash_flow"]

    def get_share_count(self, quarter: str) -> int:
        return self._historical_data[quarter]["share_count"]

    def rank(self) -> float:
        # Can handle negative growth and infinite price-to-backlog ratio
        return round((1 + self.revenue_growth_per_year()) / self.price_to_backlog_ratio(), 2)

    def price_to_revenue_ratio(self) -> float:
        last_quarter = self._get_last_quarter()
        revenue = self.get_revenue(last_quarter)

        if revenue == 0:
            return float("inf")
        
        return round(self.last_price * self.get_share_count(last_quarter) / (4 * revenue), 2)

    def price_to_backlog_ratio(self) -> float:
        if self.backlog == 0:
            return float("inf")
        
        last_quarter = self._get_last_quarter()
        return round(self.last_price * self.get_share_count(last_quarter) / self.backlog, 2)

    def revenue_growth_per_year(self) -> float:
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
            # Add $1M to every quarterly value to avoid log(0)
            np.log(revenues + 1),
            deg=1
        )[0]

        annual_growth = np.expm1(4 * quarterly_log_growth)

        return round(float(annual_growth), 2)

    def relative_hype(self) -> float:
        min = float("inf")
        max = float("-inf")
        for quarter in self._historical_data.keys():
            share_count = self.get_share_count(quarter)
            price = self.get_price(quarter)
            revenue = self.get_revenue(quarter)

            # Ignore years with 0 revenues
            if revenue == 0:
                continue

            price_to_revenue = share_count * price / (4 * revenue)

            if price_to_revenue < min:
                min = price_to_revenue

            if price_to_revenue > max:
                max = price_to_revenue

        current = share_count * self.last_price / (4 * revenue)

        return round((current - min) / (max - min), 2)

    def to_json(self) -> dict:
        price_to_revenue = self.price_to_revenue_ratio()
        if price_to_revenue == float("inf"):
            price_to_revenue = str(price_to_revenue)

        price_to_backlog = self.price_to_backlog_ratio()
        if price_to_backlog == float("inf"):
            price_to_backlog = str(price_to_backlog)
        
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
                "price_to_revenue_ratio": price_to_revenue,
                "price_to_backlog_ratio": price_to_backlog,
                "revenue_growth_per_year": self.revenue_growth_per_year(),
                "relative_hype": self.relative_hype()
            }
        }

    def _get_last_quarter(self) -> str:
        return list(self._historical_data)[-1]