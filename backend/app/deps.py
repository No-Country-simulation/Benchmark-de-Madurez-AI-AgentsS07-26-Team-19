from collections.abc import AsyncGenerator
from typing import Annotated

import asyncpg
from fastapi import Depends

from app.core.config import Settings, get_settings
from app.core.database import get_pool
from app.services.ai_client import AiClient
from app.services.pdf_client import PdfClient


async def get_db() -> AsyncGenerator[asyncpg.Pool, None]:
    yield await get_pool()


def get_pdf_client(settings: Settings = Depends(get_settings)) -> PdfClient:
    return PdfClient(settings)


def get_ai_client(settings: Settings = Depends(get_settings)) -> AiClient:
    return AiClient(settings)


DbPool = Annotated[asyncpg.Pool, Depends(get_db)]
PdfClientDep = Annotated[PdfClient, Depends(get_pdf_client)]
AiClientDep = Annotated[AiClient, Depends(get_ai_client)]