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
    # Pool pequeño por instancia: en serverless (Vercel) cada instancia abre su
    # propio pool, así que valores altos agotan las conexiones de la BD.
    postgres_min_pool_size: int = 0
    postgres_max_pool_size: int = 3
    # Supabase exige TLS; activar POSTGRES_SSL=true al apuntar a Supabase.
    postgres_ssl: bool = False

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
    # Confiar en X-Forwarded-For (solo si la API corre detrás de un proxy
    # inverso de confianza; en local y en la nube sin proxy: False).
    trust_proxy_headers: bool = False
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # Puppeteer PDF service — opcional. En producción el frontend genera el
    # PDF (impresión del navegador), así que este servicio queda vacío y el
    # endpoint /report/pdf responde 501.
    pdf_service_url: str = ""
    pdf_service_timeout_seconds: int = 30

    # AI analysis service — protocolo OpenAI-compatible (Ollama o Hugging Face
    # Inference Providers). ai_service_url apunta a base del servidor; en la
    # nube: https://router.huggingface.co. hf_token opcional: si está vacío no
    # se envía Authorization (caso Ollama local).
    ai_service_url: str = "http://localhost:11434"
    hf_token: str = ""
    ai_model: str = "hf.co/mradermacher/NeuralQwen-2.5-1.5B-Spanish-GGUF:Q4_K_M"
    ai_timeout_seconds: int = 120
    ai_max_tokens: int = 512

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_json: bool = False

    # Swagger en producción: si swagger_password no está vacío, /docs, /redoc y
    # /openapi.json se habilitan protegidos por HTTP Basic Auth (usuario
    # "swagger", password swagger_password). Vacío => docs deshabilitados.
    swagger_password: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
