from typing import List, Dict, Optional


class Borrower:
    def __init__(
        self,
        user_address: str,
        markets_in: List[str],
        borrow_balances: Dict[str, int],
        colletaral_balance: Dict[str, int],
    ):
        self.user_address = user_address
        self.markets_in = markets_in
        self.borrow_balances = borrow_balances
        self.colletaral_balance = colletaral_balance

    def _get_market_value(self, market: str, price: float) -> Dict[str, float]:
        borrow = self.borrow_balances[market] * price
        collateral = self.colletaral_balance[market] * price
        return {
            "market": market,
            "collateral": collateral / 1e18,
            "debt": borrow / 1e18,
        }

    def get_markets_values(self, prices: Dict[str, float]) -> List[Dict[str, float]]:
        return [
            self._get_market_value(market, prices[market])
            for market in self.markets_in
            if (
                market in prices
                and market in self.borrow_balances
                and market in self.colletaral_balance
                and prices[market] != 0
                and self.borrow_balances.get(market) is not None
                and self.colletaral_balance.get(market) is not None
            )
        ]
