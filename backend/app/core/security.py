import secrets
import time
from collections import defaultdict
from dataclasses import dataclass, field

from fastapi import HTTPException, Request, status


@dataclass
class RateLimitStore:
    """In-memory rate limiter (replace with Redis in production)."""

    requests: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))
    max_requests: int = 60
    window_seconds: int = 60

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        timestamps = [ts for ts in self.requests[key] if ts > window_start]
        self.requests[key] = timestamps

        if len(timestamps) >= self.max_requests:
            return False

        self.requests[key].append(now)
        return True


def generate_anon_session_id() -> str:
    return secrets.token_urlsafe(32)


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def check_rate_limit(request: Request, store: RateLimitStore) -> None:
    key = get_client_ip(request)
    if not store.is_allowed(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again later.",
        )
