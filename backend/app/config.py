import os
import sys
from pydantic_settings import BaseSettings
from functools import lru_cache


def _require_env(key: str) -> str:
    """Read required env var, crash early if missing."""
    val = os.getenv(key, "")
    if not val:
        print(f"[FATAL] Environment variable '{key}' is required but not set.", file=sys.stderr)
        sys.exit(1)
    return val


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


def validate_settings_on_startup():
    """Validate required settings at app startup. Calls sys.exit(1) if any are missing."""
    # Only validate in production (non-debug) or if explicitly running on server
    required = {
        "DATABASE_URL": os.getenv("DATABASE_URL", ""),
        "DATABASE_URL_SYNC": os.getenv("DATABASE_URL_SYNC", ""),
        "JWT_SECRET_KEY": os.getenv("JWT_SECRET_KEY", ""),
        "DEFAULT_ADMIN_PASSWORD": os.getenv("DEFAULT_ADMIN_PASSWORD", ""),
        "CLIENT_API_KEY": os.getenv("CLIENT_API_KEY", ""),
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        print(f"[FATAL] Missing required environment variables: {', '.join(missing)}", file=sys.stderr)
        print("[FATAL] Copy .env.production to .env and fill in all values.", file=sys.stderr)
        sys.exit(1)
