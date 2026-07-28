from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "NLR Diagnostic API"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "nlr"
    postgres_password: str = "nlr_secret"
    postgres_db: str = "nlr_diagnostic"
    postgres_min_pool_size: int = 2
    postgres_max_pool_size: int = 10

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def async_database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # Security
    anon_session_ttl_seconds: int = 86_400  # 24h
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # Puppeteer PDF service
    pdf_service_url: str = "http://localhost:3001"
    pdf_service_timeout_seconds: int = 30

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_json: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
