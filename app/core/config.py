import os
import pathlib
from dotenv import load_dotenv

load_dotenv()  # charge le .env avant tout os.getenv()

def _build_db_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip().strip('"')
    if url:
        return url
    user = os.getenv("POSTGRES_USER", "researchagent")
    password = os.getenv("POSTGRES_PASSWORD", "researchagent")
    db = os.getenv("POSTGRES_DB", "researchagent")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


class Settings:
    DATABASE_URL: str = _build_db_url()
    SECRET_KEY: str = os.getenv("SECRET_KEY", "a_secret_key")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    PROJECT_DIR: str = str(pathlib.Path(__file__).resolve().parents[2])
    MEMORY_PATH: str = str(pathlib.Path(PROJECT_DIR) / "app" / "memory" / "memory.json")


settings = Settings()
