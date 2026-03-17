from fastapi import FastAPI
from app.api.query import router as query_router
from app.api.auth import router as auth_router
from app.api.preferences import router as preferences_router
from app.api.preferred_links import router as preferred_links_router
from app.api.ingestion import router as ingestion_router


from app.core.logging_config import setup_logging

# Initialize logging
setup_logging()

import logging
from app.db.session import engine

logger = logging.getLogger(__name__)

app = FastAPI(
    title="research-agent",
    description="A minimal research agent API. POST questions to /query and receive a concise answer with sources.",
    version="0.1.0",
)

from fastapi.middleware.cors import CORSMiddleware

@app.on_event("startup")
def on_startup():
    try:
        with engine.connect() as conn:
            logger.info("Successfully connected to the PostgreSQL database.")
    except Exception as e:
        logger.error(f"Failed to connect to the database: {e}")

# Enable CORS with allow_credentials=True needed for cookies
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], # Add frontend origins here
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query_router, prefix="/api", tags=["query"])
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(preferences_router, prefix="/api/preferences", tags=["preferences"])
app.include_router(preferred_links_router, prefix="/api/preferred-links", tags=["preferred-links"])
app.include_router(ingestion_router, prefix="/api/ingestion", tags=["ingestion"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
