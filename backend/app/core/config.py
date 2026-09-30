from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    app_name: str = "MSME Credit Intelligence API"
    app_version: str = "1.0.0"
    app_environment: str = "development"
    app_debug: bool = True
    api_v1_prefix: str = "/api/v1"
    api_cors_origins: list[str] = ["http://localhost:4200"]

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "msme_credit_db"
    db_user: str = "msme_credit_app"
    db_password: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_minutes: int = 60
    auth_max_failed_attempts: int = 5

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
