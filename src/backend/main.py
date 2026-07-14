from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from core.agents.company_scout import CompanyScout
from database.models import create_database


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    create_database()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    company_scout = CompanyScout()
    return await company_scout.run()


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=5000)
