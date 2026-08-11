import ssl
from typing import Any

import asyncpg
from asyncpg import Pool

from app.core.config import Settings, get_settings

_pool: Pool | None = None


async def init_db_pool(settings: Settings | None = None) -> Pool:
    global _pool
    if _pool is not None:
        return _pool

    cfg = settings or get_settings()
    kwargs: dict[str, Any] = {}
    if cfg.postgres_ssl:
        if cfg.postgres_ca_cert:
            # verify-full: valida el cert del pooler (Supavisor) contra la CA
            # pública de Supabase y compara el hostname.
            ctx = ssl.create_default_context(cadata=cfg.postgres_ca_cert)
        else:
            # Sin CA configurada (POSTGRES_CA_CERT vacío): se encripta la
            # conexión pero no se valida el certificado del servidor. Setear
            # POSTGRES_CA_CERT en producción para habilitar verify-full.
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        kwargs["ssl"] = ctx

    _pool = await asyncpg.create_pool(
        dsn=cfg.async_database_url,
        min_size=cfg.postgres_min_pool_size,
        max_size=cfg.postgres_max_pool_size,
        command_timeout=60,
        # Requerido con el pooler transaction de Supabase (puerto 6543):
        # desactiva la caché de prepared statements para evitar el error
        # "prepared statement 'asyncpg_...' already exists".
        statement_cache_size=0,
        **kwargs,
    )
    return _pool


async def close_db_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def get_pool() -> Pool:
    global _pool
    if _pool is None:
        # Lazy init: en serverless (Vercel) el lifespan puede no ejecutarse en
        # cada instancia, así que el pool se crea al primer request que lo pida.
        await init_db_pool()
    assert _pool is not None
    return _pool
