class Company:
    def __init__(self,
                 name: str,
                 ticker: str,
                 last_price: int,
                 historical_prices: dict,
                 revenue: dict,
                 r_and_d_expense: dict,
                 investment_cash_flow: dict,
                 number_of_shares_outstanding_assuming_delution: dict,
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
                "number_of_shares_outstanding_assuming_delution": number_of_shares_outstanding_assuming_delution[quarter]
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
        return self._historical_data[quarter]["number_of_shares_outstanding_assuming_delution"]

    def rank(self):
        # Calculate rank
        pass

    def price_to_revenue_ratio(self):
        last_quarter = self._get_last_quarter()
        return round(self.last_price * self.get_share_count(last_quarter) / (4 * self.get_revenue(last_quarter)), 2)

    def price_to_backlog_ratio(self):
        last_quarter = self._get_last_quarter()
        return round(self.last_price * self.get_share_count(last_quarter) / self.backlog, 2)

    def get_revenue_growth_per_year(self):
        # Linear regression on log revenues then percentage per year
        pass

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

    def _get_last_quarter(self):
        return list(self._historical_data)[-1]