import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
import uvicorn

from core.tools.yahoo_finance import get_stock
from database.models import create_database
from database.database import save_stock


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    create_database()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    msft = await get_stock(ticker="MSFT")
    msft_stored = await asyncio.to_thread(save_stock, msft)

    nvda = await get_stock(ticker="NVDA")
    nvda_stored = await asyncio.to_thread(save_stock, nvda)

    return {
        "msft": {
            "id": msft_stored.id,
            "name": msft_stored.name,
            "ticker": msft_stored.ticker,
            "price_points": msft_stored.historical_prices
        },
        "nvda": {
            "id": nvda_stored.id,
            "name": nvda_stored.name,
            "ticker": nvda_stored.ticker,
            "price_points": nvda_stored.historical_prices
        }
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=5000)
