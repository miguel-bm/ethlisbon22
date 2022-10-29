from fastapi import FastAPI, Query

app = FastAPI()


@app.get("/")
async def root():
    return {"message": f"Hello World! I'm an api"}


@app.get("/getAccumulatedDebt")
async def getAccumulatedDebt(
    asset: str,
    priceDescent: float = Query(ge=0.0, le=1.0),
):
    return {
        "accumulatedLiquidations": 150234.324,
        "unit": "USD",
        "slippage": 0.02,
        "perProtocol": [
            {
                "protocol": "Compound",
                "accumulatedLiquidations": 150234.324,
                "unit": "USD",
            },
            {
                "protocol": "Euler",
                "accumulatedLiquidations": 150234.324,
                "unit": "USD",
            },
        ],
    }
