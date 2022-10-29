from typing import Union
from fastapi import FastAPI, Query
from api.models.accumulated_debt_point import AccumulatedDebtPoint
from api.utils.curve_data_loader import load_curve_data
from api.utils.curve_interpolator import interpoate_debt_curve

app = FastAPI()


@app.get("/")
async def root():
    return {"message": f"Hello World! I'm an api"}


@app.get("/getAccumulatedDebt")
async def getAccumulatedDebt(
    asset: str,
    priceDescent: float = Query(ge=0.0, le=1.0),
) -> Union[AccumulatedDebtPoint, dict]:

    curve_data = load_curve_data(asset)
    if curve_data is None:
        return {"error": f"Curve data for {asset} not found"}

    return interpoate_debt_curve(curve_data, priceDescent)
