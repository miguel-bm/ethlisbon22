from pydantic import BaseModel


class AccumulatedDebtPoint(BaseModel):
    accumulatedLiquidations: float
    unit: str
    slippage: float

    class Config:
        schema_extra = {
            "example": {
                "accumulatedLiquidations": 150234.324,
                "unit": "USD",
                "slippage": 0.02,
            }
        }
