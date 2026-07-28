from collections.abc import AsyncGenerator

import asyncpg
from fastapi import Depends, Request

from app.core.config import Settings, get_settings
from app.core.database import get_pool
from app.core.security import RateLimitStore, check_rate_limit
from app.services.pdf_client import PdfClient

_rate_limit_store: RateLimitStore | None = None


def get_rate_limit_store(settings: Settings = Depends(get_settings)) -> RateLimitStore:
    global _rate_limit_store
    if _rate_limit_store is None:
        _rate_limit_store = RateLimitStore(
            max_requests=settings.rate_limit_requests,
            window_seconds=settings.rate_limit_window_seconds,
        )
    return _rate_limit_store


async def get_db() -> AsyncGenerator[asyncpg.Pool, None]:
    yield get_pool()


def get_pdf_client(settings: Settings = Depends(get_settings)) -> PdfClient:
    return PdfClient(settings)


async def rate_limit_dependency(
    request: Request,
    store: RateLimitStore = Depends(get_rate_limit_store),
) -> None:
    check_rate_limit(request, store)
