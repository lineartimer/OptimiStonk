import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException

from core.tools.yahoo_finance import get_stock
from database.models import create_database
from database.database import save_stock


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    create_database()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root(ticker: str = "MSFT"):
    try:
        downloaded_stock = await get_stock(ticker)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"Could not download data for ticker {ticker}",
        ) from error

    stored_stock = await asyncio.to_thread(save_stock, downloaded_stock)
    latest_price = max(
        stored_stock.historical_prices,
        key=lambda historical_price: historical_price.price_date,
    )

    return {
        "id": stored_stock.id,
        "name": stored_stock.name,
        "ticker": stored_stock.ticker,
        "price_points": len(stored_stock.historical_prices),
        "latest_price": latest_price.price,
        "latest_price_date": latest_price.price_date,
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=5000)
