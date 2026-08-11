import secrets

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import get_settings


def generate_anon_session_id() -> str:
    # token_urlsafe(24) -> 32 chars, justo el máximo de
    # benchmark_response.anonymous_code (VARCHAR(32)).
    return secrets.token_urlsafe(24)


def get_client_ip(request: Request) -> str:
    # Solo confiar en X-Forwarded-For si corremos detrás de un proxy inverso
    # de confianza (TRUST_PROXY_HEADERS=true). En local, cualquier cliente
    # puede falsificar ese header y eludir el rate limit.
    if get_settings().trust_proxy_headers:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return get_remote_address(request)


_settings = get_settings()
RATE_LIMIT = f"{_settings.rate_limit_requests}/{_settings.rate_limit_window_seconds}second"

limiter = Limiter(
    key_func=get_client_ip,
    # Per-route decorators use RATE_LIMIT; default_limits is intentionally
    # empty so health checks and un-decorated routes are not rate-limited.
    headers_enabled=False,
    strategy="moving-window",
)
