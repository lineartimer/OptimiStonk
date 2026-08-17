from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from edgar import set_identity
from fastapi import FastAPI
import os
import uvicorn

from core.tools.financials import get_financials


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    set_identity(os.getenv("EDGAR_IDENTITY"))
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {
        "MSFT": await get_financials("MSFT")
        # "NVDA": await get_financials("NVDA")
        # "IREN": await get_financials("IREN")
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=5000)
