from fastapi import FastAPI
from app.api.query import router as query_router

app = FastAPI(title="research-agent")
app.include_router(query_router, prefix="")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
