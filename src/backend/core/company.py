import math
import numpy as np


class Company:
    def __init__(self,
                 name: str,
                 ticker: str,
                 last_price: int,
                 revenue: dict,
                 r_and_d_expense: dict,
                 investment_cash_flow: dict,
                 share_count: dict,
                 backlog: int,
                 summary: str,
                 historical_prices: dict
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
        self.summary = summary

    def get_price(self, quarter: str) -> int | None:
        return self._historical_data.get(quarter, {}).get("price")

    def get_revenue(self, quarter: str) -> int | None:
        return self._historical_data.get(quarter, {}).get("revenue")

    def get_r_and_d_expense(self, quarter: str) -> int | None:
        return self._historical_data.get(quarter, {}).get("r_and_d_expense")

    def get_investment_cash_flow(self, quarter: str) -> int | None:
        return self._historical_data.get(quarter, {}).get("investment_cash_flow")

    def get_share_count(self, quarter: str) -> int | None:
        return self._historical_data.get(quarter, {}).get("share_count")

    def rank_market(self) -> float:
        revenue_growth_per_year = self.revenue_growth_per_year()
        price_to_revenue_ratio = self.price_to_revenue_ratio()

        if not revenue_growth_per_year or not price_to_revenue_ratio:
            return None

        return round(revenue_growth_per_year / price_to_revenue_ratio, 4)

    def rank_backlog(self) -> float:
        revenue_growth_per_year = self.revenue_growth_per_year()
        price_to_backlog_ratio = self.price_to_backlog_ratio()

        # Can handle negative growth and infinite price-to-backlog ratio
        return round((1 + revenue_growth_per_year) / price_to_backlog_ratio, 4)

    def price_to_revenue_ratio(self) -> float:
        last_quarter = self._get_last_quarter()
        revenue = self.get_revenue(last_quarter)

        if not last_quarter:
            return None

        if revenue == 0:
            return float("inf")
        
        return round(self.last_price * self.get_share_count(last_quarter) / (4 * revenue), 2)

    def price_to_backlog_ratio(self) -> float:
        last_quarter = self._get_last_quarter()
        if not last_quarter:
            return None
        
        if self.backlog == 0:
            return float("inf")
        
        return round(self.last_price * self.get_share_count(last_quarter) / self.backlog, 2)

    def revenue_growth_per_year(self) -> float:
        if len(self._historical_data) < 2:
            return None
        
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

        return round(float(annual_growth), 4)

    def relative_hype(self) -> float:
        if len(self._historical_data) == 0:
            return None
        
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

        if revenue == 0:
            current = float("inf")
        else:
            current = share_count * self.last_price / (4 * revenue)

        return round((current - min) / (max - min), 4)

    def to_json(self) -> dict:
        price_to_revenue = self.price_to_revenue_ratio()
        price_to_backlog = self.price_to_backlog_ratio()
        relative_hype = self.relative_hype()
        
        return {
            "name": self.name,
            "ticker": self.ticker,
            "last_price": self.last_price,
            "summary": self.summary,
            "rank_market": self.rank_market(),
            "rank_backlog": self.rank_backlog(),
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
                "price_to_revenue_ratio": self._normalize_for_json(price_to_revenue),
                "price_to_backlog_ratio": self._normalize_for_json(price_to_backlog),
                "revenue_growth_per_year": self.revenue_growth_per_year(),
                "relative_hype": self._normalize_for_json(relative_hype)
            }
        }

    def _get_last_quarter(self) -> str:
        return list(self._historical_data)[-1] if self._historical_data else None

    def _normalize_for_json(self, input: float) -> float | str:
        if input in [float("inf"), float("-inf")] or math.isnan(input):
            return str(input)

        return input