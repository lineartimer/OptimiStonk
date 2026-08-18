from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from edgar import set_identity
from fastapi import FastAPI
import os
import uvicorn

from backend.financials import get_financials
from backend.db.database import initialize_database


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    set_identity(os.getenv("EDGAR_IDENTITY"))
    initialize_database()
    
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/get_stock")
async def get_stock(ticker: str):
    ticker = ticker.strip().upper()
    stock = await get_financials(ticker)

    return stock.to_json()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=5000)
