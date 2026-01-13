from fastapi import FastAPI
from app.api.query import router as query_router


app = FastAPI(
    title="research-agent",
    description="A minimal research agent API. POST questions to /query and receive a concise answer with sources.",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)
app.include_router(query_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
