from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from edgar import set_identity
from fastapi import FastAPI
import os
import uvicorn

from backend.api.discover import discovery_router
from backend.api.market import market_router
from backend.api.search import search_router
from backend.api.stock import stock_router
from backend.core.tools.web import web_session
from backend.database.database import initialize_database


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    set_identity(os.getenv("EDGAR_IDENTITY"))

    # One browser (and its cookies) will be shared for the application's lifetime
    async with web_session():
        await initialize_database()
        yield


app = FastAPI(lifespan=lifespan)

app.include_router(discovery_router)
app.include_router(market_router)
app.include_router(search_router)
app.include_router(stock_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000)
