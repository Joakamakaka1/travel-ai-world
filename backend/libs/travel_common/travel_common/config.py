"""Settings every service shares. Each service subclasses and adds its own."""

from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict


class CommonSettings(BaseSettings):
    PROJECT_NAME: str = "Travel AI World"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # CORS — list allowed frontend origins explicitly in production.
    # allow_credentials=True forbids "*", so this must never be a wildcard.
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # JWT. SECRET_KEY must be identical in every service that verifies tokens.
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Frontend URL (for redirects / CORS)
    FRONTEND_URL: str = "http://localhost:3000"

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )
