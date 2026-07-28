import asyncpg
from asyncpg import Pool

from app.core.config import Settings, get_settings

_pool: Pool | None = None


async def init_db_pool(settings: Settings | None = None) -> Pool:
    global _pool
    if _pool is not None:
        return _pool

    cfg = settings or get_settings()
    _pool = await asyncpg.create_pool(
        dsn=cfg.async_database_url,
        min_size=cfg.postgres_min_pool_size,
        max_size=cfg.postgres_max_pool_size,
        command_timeout=60,
    )
    return _pool


async def close_db_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> Pool:
    if _pool is None:
        raise RuntimeError("Database pool is not initialized")
    return _pool
