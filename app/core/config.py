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
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    PROJECT_DIR: str = str(pathlib.Path(__file__).resolve().parents[2])
    MEMORY_PATH: str = str(pathlib.Path(PROJECT_DIR) / "app" / "memory" / "memory.json")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_API_URL: str = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1")
    DEFAULT_AI_MODEL: str = os.getenv("DEFAULT_AI_MODEL", "google/gemini-2.5-flash")
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_URL: str = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1")
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")


settings = Settings()
