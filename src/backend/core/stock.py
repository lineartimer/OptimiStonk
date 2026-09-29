import math
import numpy as np


class StockError(ValueError):
    pass


class Stock:
    def __init__(self,
                 name: str,
                 ticker: str,
                 last_price: int,
                 revenue: dict,
                 r_and_d_expense: dict,
                 operating_income: dict,
                 cash_and_equivalents: dict,
                 investment_cash_flow: dict,
                 share_count: dict,
                 backlog: int,
                 summary: str,
                 historical_prices: dict
    ):
        if (len(revenue) < 2 or
            len(r_and_d_expense) < 2 or
            len(operating_income) < 2 or
            len(cash_and_equivalents) < 2 or
            len(investment_cash_flow) < 2 or
            len(share_count) < 2 or
            len(historical_prices) < 2
        ):
            raise StockError(f"{ticker} has less than 2 quarters of financial data.")

        self.name = name
        self.ticker = ticker
        self.last_price = last_price

        self._historical_data = {}

        for quarter in revenue.keys():
            self._historical_data[quarter] = {
                "price": historical_prices[quarter],
                "revenue": revenue[quarter],
                "r_and_d_expense": r_and_d_expense[quarter],
                "operating_income": operating_income[quarter],
                "cash_and_equivalents": cash_and_equivalents[quarter],
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

    def get_operating_income(self, quarter: str) -> int | None:
        return self._historical_data.get(quarter, {}).get("operating_income")

    def get_cash_and_equivalents(self, quarter: str) -> int | None:
        return self._historical_data.get(quarter, {}).get("cash_and_equivalents")

    def get_investment_cash_flow(self, quarter: str) -> int | None:
        return self._historical_data.get(quarter, {}).get("investment_cash_flow")

    def get_share_count(self, quarter: str) -> int | None:
        return self._historical_data.get(quarter, {}).get("share_count")

    def get_average_revenue(self) -> float:
        return self._get_average_value("revenue")

    def get_average_r_and_d_expense(self) -> float:
        return self._get_average_value("r_and_d_expense")

    def get_average_operating_income(self) -> float:
        return self._get_average_value("operating_income")

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
        
        return round(
            self.last_price * self.get_share_count(last_quarter) / (4 * revenue),
            2
        )

    def price_to_backlog_ratio(self) -> float:
        last_quarter = self._get_last_quarter()
        if not last_quarter:
            return None
        
        if self.backlog == 0:
            return float("inf")
        
        return round(
            self.last_price * self.get_share_count(last_quarter) / self.backlog,
            2
        )

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

    def to_json(self) -> dict:
        price_to_revenue = self.price_to_revenue_ratio()
        price_to_backlog = self.price_to_backlog_ratio()
        
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
                    "operating_income": data["operating_income"],
                    "cash_and_equivalents": data["cash_and_equivalents"],
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
                "revenue_growth_per_year": self.revenue_growth_per_year()
            }
        }

    def _get_last_quarter(self) -> str:
        return list(self._historical_data)[-1] if self._historical_data else None
    
    def _get_average_value(self, key: str) -> float:
        return sum(
            data[key] for data in self._historical_data.values()
        ) / len(self._historical_data)

    def _normalize_for_json(self, input: float | None) -> float | str | None:
        if input is None:
            return None

        if input in [float("inf"), float("-inf")] or math.isnan(input):
            return str(input)

        return input
