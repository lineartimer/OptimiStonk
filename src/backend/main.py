from fastapi import FastAPI
import uvicorn


from core.agents.company_scout import CompanyScout
from core.tools.web import load_web_page


app = FastAPI()


@app.get("/")
async def root():
    page = await load_web_page("https://search.brave.com/search?q=Nasdaq")
    return page

    # company_scout = CompanyScout()
    # return await company_scout.run()


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=5000)
