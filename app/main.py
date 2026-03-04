from fastapi import FastAPI
from app.api.query import router as query_router
from app.api.auth import router as auth_router
from app.api.preferences import router as preferences_router


import logging
from app.db.session import engine

logger = logging.getLogger(__name__)

app = FastAPI(
    title="research-agent",
    description="A minimal research agent API. POST questions to /query and receive a concise answer with sources.",
    version="0.1.0",
)

@app.on_event("startup")
def on_startup():
    try:
        with engine.connect() as conn:
            logger.info("Successfully connected to the PostgreSQL database.")
    except Exception as e:
        logger.error(f"Failed to connect to the database: {e}")

app.include_router(query_router, prefix="/api", tags=["query"])
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(preferences_router, prefix="/api/preferences", tags=["preferences"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
