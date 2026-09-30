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
                 net_income: dict,
                 eps: dict,
                 cash_and_equivalents: dict,
                 marketable_securities: dict,
                 accounts_receivable: dict,
                 total_assets: dict,
                 current_liabilities: dict,
                 long_term_debt: dict,
                 shareholders_equity: dict,
                 investment_cash_flow: dict,
                 share_count: dict,
                 backlog: int,
                 summary: str,
                 historical_prices: dict
    ):
        if (len(revenue) < 2 or
            len(r_and_d_expense) < 2 or
            len(operating_income) < 2 or
            len(net_income) < 2 or
            len(eps) < 2 or
            len(cash_and_equivalents) < 2 or
            len(marketable_securities) < 2 or
            len(accounts_receivable) < 2 or
            len(total_assets) < 2 or
            len(current_liabilities) < 2 or
            len(long_term_debt) < 2 or
            len(shareholders_equity) < 2 or
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
                "net_income": net_income[quarter],
                "eps": eps[quarter],
                "cash_and_equivalents": cash_and_equivalents[quarter],
                "marketable_securities": marketable_securities[quarter],
                "accounts_receivable": accounts_receivable[quarter],
                "total_assets": total_assets[quarter],
                "current_liabilities": current_liabilities[quarter],
                "long_term_debt": long_term_debt[quarter],
                "shareholders_equity": shareholders_equity[quarter],
                "investment_cash_flow": investment_cash_flow[quarter],
                "share_count": share_count[quarter]
            }

        self.backlog = backlog
        self.summary = summary

    # Price
    def get_price(self, quarter: str) -> int | None:
        return self._historical_data.get(quarter, {}).get("price")

    # Income statement
    def get_revenue(self, quarter: str) -> int | None:
        return self._historical_data.get(quarter, {}).get("revenue")

    def get_r_and_d_expense(self, quarter: str) -> int | None:
        return self._historical_data.get(quarter, {}).get("r_and_d_expense")

    def get_operating_income(self, quarter: str) -> int | None:
        return self._historical_data.get(quarter, {}).get("operating_income")

    def get_net_income(self, quarter: str) -> int | None:
        return self._historical_data.get(quarter, {}).get("net_income")

    def get_eps(self, quarter: str) -> float | None:
        return self._historical_data.get(quarter, {}).get("eps")

    # Balance sheet
    def get_cash_and_equivalents(self, quarter: str) -> int | None:
        return self._historical_data.get(quarter, {}).get("cash_and_equivalents")

    def get_marketable_securities(self, quarter: str) -> int | None:
        return self._historical_data.get(quarter, {}).get("marketable_securities")

    def get_accounts_receivable(self, quarter: str) -> int | None:
        return self._historical_data.get(quarter, {}).get("accounts_receivable")

    def get_total_assets(self, quarter: str) -> int | None:
        return self._historical_data.get(quarter, {}).get("total_assets")

    def get_current_liabilities(self, quarter: str) -> int | None:
        return self._historical_data.get(quarter, {}).get("current_liabilities")

    def get_long_term_debt(self, quarter: str) -> int | None:
        return self._historical_data.get(quarter, {}).get("long_term_debt")

    def get_shareholders_equity(self, quarter: str) -> int | None:
        return self._historical_data.get(quarter, {}).get("shareholders_equity")

    # Cash flow
    def get_investment_cash_flow(self, quarter: str) -> int | None:
        return self._historical_data.get(quarter, {}).get("investment_cash_flow")

    # Share count
    def get_share_count(self, quarter: str) -> int | None:
        return self._historical_data.get(quarter, {}).get("share_count")

    # Averages of financial data
    def get_average_revenue(self, years: int = 5) -> float:
        return self._get_average_value("revenue", years)

    def get_average_r_and_d_expense(self, years: int = 5) -> float:
        return self._get_average_value("r_and_d_expense", years)

    def get_average_operating_income(self, years: int = 5) -> float:
        return self._get_average_value("operating_income", years)

    def get_average_eps(self, years: int = 5) -> float:
        return self._get_average_value("eps", years)

    # Ratios
    def quick_ratio(self) -> float:
        last_quarter = self._get_last_quarter()

        current_liabilities = self.get_current_liabilities(last_quarter)
        if current_liabilities == 0:
            return float("inf")

        return round((
            self.get_cash_and_equivalents(last_quarter) +
            self.get_marketable_securities(last_quarter) +
            self.get_accounts_receivable(last_quarter)
        ) / current_liabilities, 2)

    def leverage(self) -> float:
        last_quarter = self._get_last_quarter()

        shareholders_equity = self.get_shareholders_equity(last_quarter)
        if shareholders_equity == 0:
            return float("inf")

        return round(
            self.get_total_assets(last_quarter) / shareholders_equity,
            2
        )

    def asset_turnover(self) -> float:
        last_quarter = self._get_last_quarter()

        total_assets = self.get_total_assets(last_quarter)
        if total_assets == 0:
            return float("inf")

        return round(
            self.get_average_revenue() / total_assets,
            2
        )

    def operating_margin(self) -> float:
        average_revenue = self.get_average_revenue()
        if average_revenue == 0:
            return 0.0

        return round(
            self.get_average_operating_income() / average_revenue,
            2
        )

    def r_and_d_to_revenue(self) -> float:
        average_revenue = self.get_average_revenue()
        if average_revenue == 0:
            return 0.0

        return round(
            self.get_average_r_and_d_expense() / average_revenue,
            2
        )

    def price_to_earnings_ratio(self) -> float:
        average_eps = 4 * self.get_average_eps()
        if average_eps == 0:
            return float("inf")

        return round(self.last_price / average_eps, 2)

    def price_to_revenue_ratio(self) -> float:
        last_quarter = self._get_last_quarter()

        revenue = self.get_revenue(last_quarter)
        if revenue == 0:
            return float("inf")
        
        return round(
            self.last_price * self.get_share_count(last_quarter) / (4 * revenue),
            2
        )

    def price_to_backlog_ratio(self) -> float:
        last_quarter = self._get_last_quarter()
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

    def financial_strength(self):
        return (
            self.quick_ratio() / # Cash is good
            self.leverage() * # Debt is bad
            self.asset_turnover() * # Ability to turn assets to revenue is good
            self.operating_margin() * # A high margin is good
            self.get_average_revenue() # The bigger the company, the more resilient
        )

    # Rank
    def rank(self) -> float:
        rank_raw = (
            1_000_000_000 *
            self.revenue_growth_per_year() * # A growing top line is good
            (0.01 + self.r_and_d_to_revenue()) * # R&D is good
            self.financial_strength() ** 2  / # Financial strength is even better
            self.price_to_earnings_ratio() ** 4 # A low valuation is the best
        )

        if rank_raw <= 0:
            return float("-inf")

        return math.log(rank_raw)

    def to_json(self) -> dict:
        price_to_earnings_ratio = self.price_to_earnings_ratio()
        revenue_growth_per_year = self.revenue_growth_per_year()
        quick_ratio = self.quick_ratio()
        leverage = self.leverage()
        asset_turnover = self.asset_turnover()
        
        return {
            "name": self.name,
            "ticker": self.ticker,
            "last_price": self.last_price,
            "summary": self.summary,
            "rank": self._normalize_for_json(self.rank()),
            "backlog": self.backlog,
            "financial_data": {
                quarter: {
                    "revenue": data["revenue"],
                    "r_and_d_expense": data["r_and_d_expense"],
                    "operating_income": data["operating_income"],
                    "net_income": data["net_income"],
                    "eps": data["eps"],
                    "cash_and_equivalents": data["cash_and_equivalents"],
                    "marketable_securities": data["marketable_securities"],
                    "accounts_receivable": data["accounts_receivable"],
                    "total_assets": data["total_assets"],
                    "current_liabilities": data["current_liabilities"],
                    "long_term_debt": data["long_term_debt"],
                    "shareholders_equity": data["shareholders_equity"],
                    "investment_cash_flow": data["investment_cash_flow"],
                    "share_count": data["share_count"]
                } for quarter, data in self._historical_data.items()
            },
            "historical_prices": {
                quarter: data["price"] for quarter, data in self._historical_data.items()
            },
            "ratios": {
                "price_to_earnings_ratio": self._normalize_for_json(price_to_earnings_ratio),
                "revenue_growth_per_year": self._normalize_for_json(revenue_growth_per_year),
                "quick_ratio": self._normalize_for_json(quick_ratio),
                "leverage": self._normalize_for_json(leverage),
                "asset_turnover": self._normalize_for_json(asset_turnover),
                "operating_margin": self._normalize_for_json(self.operating_margin()),
                "r_and_d_to_revenue": self._normalize_for_json(self.r_and_d_to_revenue())
            }
        }

    def _get_last_quarter(self) -> str:
        return list(self._historical_data)[-1] if self._historical_data else None
    
    def _get_average_value(self, key: str, years: int) -> float:
        quarters = sorted(self._historical_data)
        if years is not None:
            quarters = quarters[-4 * years:]

        return sum(
            self._historical_data[quarter][key] for quarter in quarters
        ) / len(quarters)

    def _normalize_for_json(self, input: float | None) -> float | str | None:
        if input is None:
            return None

        if input in [float("inf"), float("-inf")] or math.isnan(input):
            return str(input)

        return input
