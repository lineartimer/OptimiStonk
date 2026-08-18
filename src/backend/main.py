from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from edgar import set_identity
from fastapi import FastAPI
import os
import uvicorn

from backend.financials import get_financials


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    set_identity(os.getenv("EDGAR_IDENTITY"))
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    msft = await get_financials("MSFT")
    nvda = await get_financials("NVDA")
    iren = await get_financials("IREN")

    return {
        "MSFT": {
            "rank": msft.rank(),
            "price_to_backlog": msft.price_to_backlog_ratio(),
            "revenue_growth_per_year": msft.revenue_growth_per_year(),
            "price_to_revenue": msft.price_to_revenue_ratio(),
            "relative_hype": msft.relative_hype()
        },
        "NVDA": {
            "rank": nvda.rank(),
            "price_to_backlog": nvda.price_to_backlog_ratio(),
            "revenue_growth_per_year": nvda.revenue_growth_per_year(),
            "price_to_revenue": nvda.price_to_revenue_ratio(),
            "relative_hype": nvda.relative_hype()
        },
        "IREN": {
            "rank": iren.rank(),
            "price_to_backlog": iren.price_to_backlog_ratio(),
            "revenue_growth_per_year": iren.revenue_growth_per_year(),
            "price_to_revenue": iren.price_to_revenue_ratio(),
            "relative_hype": iren.relative_hype()
        }
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=5000)
