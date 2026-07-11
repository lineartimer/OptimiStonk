from fastapi import FastAPI
import uvicorn


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    # Only run this if the file is executed directly, not when imported as a module
    uvicorn.run("main:app", port=5000)