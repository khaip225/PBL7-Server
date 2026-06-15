import os
from pydantic_settings import BaseSettings
from functools import lru_cache



class Settings(BaseSettings):
    APP_NAME: str = "PBL7 FL Control Center"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    DATABASE_URL_SYNC: str = os.getenv("DATABASE_URL_SYNC", "")
    FLOWER_SERVER_DIR: str = "flower_server"
    MODELS_DIR: str = "aggregated_models"
    WS_HEARTBEAT_INTERVAL: int = 30
    CLIENT_TIMEOUT_SECONDS: int = 60
    MAX_CONCURRENT_JOBS: int = 2
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480
    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = os.getenv("DEFAULT_ADMIN_PASSWORD", "")
    CLIENT_API_KEY: str = os.getenv("CLIENT_API_KEY", "")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()




