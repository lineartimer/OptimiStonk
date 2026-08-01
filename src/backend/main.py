from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from edgar import set_identity
from fastapi import FastAPI
import os
import uvicorn

from core.tools.financials import get_financials
from database.models import create_database


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    create_database()

    set_identity(os.getenv("EDGAR_IDENTITY"))
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return await get_financials("NVDA")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=5000)
