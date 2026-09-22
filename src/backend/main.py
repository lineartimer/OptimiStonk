from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from edgar import set_identity
from fastapi import FastAPI
import os
import uvicorn

from backend.api.companies import router as companies_router
from backend.api.get_stock import router as get_stock_router
from backend.api.scout import router as scout_router
from backend.database.database import initialize_database


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    set_identity(os.getenv("EDGAR_IDENTITY"))
    await initialize_database()

    yield


app = FastAPI(lifespan=lifespan)
app.include_router(companies_router)
app.include_router(get_stock_router)
app.include_router(scout_router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000)
