import secrets

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import get_settings


def generate_anon_session_id() -> str:
    return secrets.token_urlsafe(32)


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


_settings = get_settings()
limiter = Limiter(
    key_func=get_client_ip,
    default_limits=[f"{_settings.rate_limit_requests}/{_settings.rate_limit_window_seconds}second"],
    # headers_enabled would require every endpoint to return a raw Response;
    # our handlers return Pydantic models via response_model, so keep it off.
    headers_enabled=False,
    strategy="moving-window",
)
