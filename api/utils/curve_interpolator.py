from api.models.accumulated_debt_point import AccumulatedDebtPoint


def interpoate_debt_curve(
    curve_data: dict, price_descent: float
) -> AccumulatedDebtPoint:
    return AccumulatedDebtPoint(
        accumulatedLiquidations=0.0,
        unit="USD",
        slippage=0.0,
    )
