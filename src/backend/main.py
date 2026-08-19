from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from edgar import set_identity
from fastapi import FastAPI
import os
import uvicorn

from backend.api.get_stock import router as get_stock_router
from backend.db.database import initialize_database


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    set_identity(os.getenv("EDGAR_IDENTITY"))
    await initialize_database()

    yield


app = FastAPI(lifespan=lifespan)
app.include_router(get_stock_router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=5000)
