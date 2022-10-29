from api.models.accumulated_debt_point import AccumulatedDebtPoint


def interpoate_debt_curve(
    curve_data: dict, price_descent: float
) -> AccumulatedDebtPoint:
    for data_point in curve_data:
        if data_point["price_change"] >= price_descent:
            total_liquidation = data_point["total_liquidation"]
            slippage = data_point["liquidation_slippage"]
            return AccumulatedDebtPoint(
                accumulatedLiquidations=str(int(total_liquidation * 1e18)),
                unit="USD",
                slippage=str(int(slippage * 1e18)),
            )
