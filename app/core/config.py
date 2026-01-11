from pydantic import BaseSettings
import pathlib


class Settings(BaseSettings):
    PROJECT_DIR: str = str(pathlib.Path(__file__).resolve().parents[2])
    MEMORY_PATH: str = str(pathlib.Path(PROJECT_DIR) / "app" / "memory" / "memory.json")


settings = Settings()
