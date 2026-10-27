import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Root directory of the backend or repository
BASE_DIR = Path(__file__).resolve().parent
PARENT_ENV = BASE_DIR.parent / ".env"
LOCAL_ENV = BASE_DIR / ".env"

env_file_path = LOCAL_ENV if LOCAL_ENV.exists() else PARENT_ENV

class Settings(BaseSettings):
    PROJECT_NAME: str = "Транспорт Севера API"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"

    # Host & Port (Render/Railway sets PORT environment variable automatically)
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT", "8000"))

    # MongoDB connection
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "transport_severa"

    # JWT Authentication
    JWT_SECRET: str = "секретный-ключ-транспорт-севера-2026-супер-надежно"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # External APIs
    YANDEX_RASP_API_KEY: str = ""
    YANDEX_RASP_BASE_URL: str = "https://api.rasp.yandex.net/v3.0"
    
    # Weather API (Open-Meteo is free without API key, plus simulated Arctic conditions fallback)
    OPEN_METEO_BASE_URL: str = "https://api.open-meteo.com/v1"

    # CORS settings (allowed origins for frontend, wildcard for easy deployment)
    CORS_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = str(env_file_path)
        extra = "allow"

settings = Settings()
