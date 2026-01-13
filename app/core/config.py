# try:
#     from pydantic_settings import BaseSettings
# except ImportError:
#     from pydantic import BaseSettings

from pydantic_settings import BaseSettings
import pathlib


class Settings(BaseSettings):
    PROJECT_DIR: str = str(pathlib.Path(__file__).resolve().parents[2])
    MEMORY_PATH: str = str(pathlib.Path(PROJECT_DIR) / "app" / "memory" / "memory.json")


settings = Settings()
