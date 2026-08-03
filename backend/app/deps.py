from collections.abc import AsyncGenerator

import asyncpg
from fastapi import Depends

from app.core.config import Settings, get_settings
from app.core.database import get_pool
from app.services.pdf_client import PdfClient


async def get_db() -> AsyncGenerator[asyncpg.Pool, None]:
    yield get_pool()


def get_pdf_client(settings: Settings = Depends(get_settings)) -> PdfClient:
    return PdfClient(settings)
