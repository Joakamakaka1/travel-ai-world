from functools import lru_cache
from typing import Literal

from travel_common.config import CommonSettings


class CoreSettings(CommonSettings):
    PROJECT_NAME: str = "Travel AI World — Core API"

    # DB Engine Selection (postgresql, mysql, sqlite)
    DB_ENGINE: Literal["postgresql", "mysql", "sqlite"] = "postgresql"

    # Database Config (Postgres & MySQL)
    DB_SERVER: str = "127.0.0.1"
    DB_USER: str = ""
    DB_PASSWORD: str = ""
    DB_NAME: str = "fastapi_db"
    DB_PORT: int = 5432

    # SQLite Config
    SQLITE_FILE: str = "sqlite.db"

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.DB_ENGINE == "postgresql":
            return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_SERVER}:{self.DB_PORT}/{self.DB_NAME}"
        elif self.DB_ENGINE == "mysql":
            return f"mysql+asyncmy://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_SERVER}:{self.DB_PORT}/{self.DB_NAME}"
        else:  # sqlite
            return f"sqlite+aiosqlite:///{self.SQLITE_FILE}"

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # NVIDIA AI Chat (moves to ai_api)
    NVIDIA_API_KEY: str = ""


@lru_cache
def get_settings() -> CoreSettings:
    return CoreSettings()


settings = get_settings()
