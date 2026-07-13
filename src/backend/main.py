from fastapi import FastAPI
import uvicorn

from core.agents.company_scout import CompanyScout


app = FastAPI()


@app.get("/")
async def root():
    company_scout = CompanyScout()
    return await company_scout.run()


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=5000)
