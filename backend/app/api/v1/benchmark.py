import asyncpg
from fastapi import APIRouter, Depends

from app.deps import get_db, rate_limit_dependency
from app.models.schemas import (
    BenchmarkQuestion,
    BenchmarkStats,
    Dimension,
    PercentileLookupRequest,
    PercentileLookupResponse,
)
from app.services import benchmark_engine, percentiles

router = APIRouter(prefix="/benchmark", tags=["benchmark"])


@router.get(
    "/questions",
    response_model=list[BenchmarkQuestion],
    dependencies=[Depends(rate_limit_dependency)],
)
async def list_questions(
    pool: asyncpg.Pool = Depends(get_db),
) -> list[BenchmarkQuestion]:
    return await benchmark_engine.get_questions(pool)


@router.get(
    "/stats",
    response_model=list[BenchmarkStats],
    dependencies=[Depends(rate_limit_dependency)],
)
async def get_stats(
    pool: asyncpg.Pool = Depends(get_db),
) -> list[BenchmarkStats]:
    rows = await pool.fetch(
        """
        SELECT dimension,
               AVG(score) AS mean,
               STDDEV(score) AS std_dev,
               COUNT(*) AS sample_size
        FROM benchmark_scores
        GROUP BY dimension
        ORDER BY dimension
        """
    )
    return [
        BenchmarkStats(
            dimension=Dimension(row["dimension"]),
            mean=round(float(row["mean"]), 2),
            std_dev=round(float(row["std_dev"] or 0), 2),
            sample_size=row["sample_size"],
        )
        for row in rows
    ]


@router.get(
    "/percentiles",
    dependencies=[Depends(rate_limit_dependency)],
)
async def list_percentiles(
    pool: asyncpg.Pool = Depends(get_db),
) -> list[dict]:
    return await percentiles.get_all_percentiles(pool)


@router.post(
    "/percentiles/lookup",
    response_model=PercentileLookupResponse,
    dependencies=[Depends(rate_limit_dependency)],
)
async def lookup_percentile(
    payload: PercentileLookupRequest,
    pool: asyncpg.Pool = Depends(get_db),
) -> PercentileLookupResponse:
    percentile = await percentiles.get_percentile(
        pool, payload.dimension, payload.score
    )
    return PercentileLookupResponse(
        dimension=payload.dimension,
        score=payload.score,
        percentile=percentile,
    )
