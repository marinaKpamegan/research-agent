# try:
#     from pydantic_settings import BaseSettings
# except ImportError:
#     from pydantic import BaseSettings

from pydantic_settings import BaseSettings
import pathlib


class Settings(BaseSettings):
    SECRET_KEY: str = "a_secret_key"
    DATABASE_URL: str = "sqlite:///./test.db"
    PROJECT_DIR: str = str(pathlib.Path(__file__).resolve().parents[2])
    MEMORY_PATH: str = str(pathlib.Path(PROJECT_DIR) / "app" / "memory" / "memory.json")
    ALGORITHM: str = "HS256"


settings = Settings()
