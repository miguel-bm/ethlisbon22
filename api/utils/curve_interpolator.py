from api.models.accumulated_debt_point import AccumulatedDebtPoint


def interpoate_debt_curve(
    curve_data: dict, price_descent: float
) -> AccumulatedDebtPoint:
    for data_point in curve_data:
        if data_point["price_change"] >= price_descent:
            return AccumulatedDebtPoint(
                accumulatedLiquidations=data_point["total_liquidation"],
                unit="USD",
                slippage=data_point["liquidation_slippage"],
            )
