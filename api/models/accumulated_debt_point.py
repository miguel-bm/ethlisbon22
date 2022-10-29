from pydantic import BaseModel


class AccumulatedDebtPoint(BaseModel):
    accumulatedLiquidations: str
    unit: str
    slippage: str

    class Config:
        schema_extra = {
            "example": {
                "accumulatedLiquidations": "15023432475928445910365",
                "unit": "USD",
                "slippage": "230194665941057366",
            }
        }
