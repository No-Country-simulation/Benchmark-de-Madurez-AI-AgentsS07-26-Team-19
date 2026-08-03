"""Benchmark endpoints -- questions, stats, percentile lookup, and weights."""

import asyncpg
from fastapi import APIRouter, Depends, Request

from app.core.security import limiter
from app.deps import get_db
from app.models.schemas import (
    BenchmarkQuestion,
    BenchmarkStats,
    Dimension,
    PercentileLookupRequest,
    PercentileLookupResponse,
    WeightsResponse,
)
from app.services import benchmark_engine, percentiles
from app.services.rebalancing import get_current_weights

router = APIRouter(prefix="/benchmark", tags=["benchmark"])


@router.get(
    "/questions",
    response_model=list[BenchmarkQuestion],
    summary="List all benchmark questions",
)
@limiter.limit("60/minute")
async def list_questions(
    request: Request,
    pool: asyncpg.Pool = Depends(get_db),
) -> list[BenchmarkQuestion]:
    return await benchmark_engine.get_questions(pool)


@router.get(
    "/stats",
    response_model=list[BenchmarkStats],
    summary="Get population statistics per dimension",
    description="Returns mean, standard deviation, and sample size for each dimension.",
)
@limiter.limit("60/minute")
async def get_stats(
    request: Request,
    pool: asyncpg.Pool = Depends(get_db),
) -> list[BenchmarkStats]:
    rows = await pool.fetch(
        """
        SELECT dimension,
               AVG(score)    AS mean,
               STDDEV(score) AS std_dev,
               COUNT(*)      AS sample_size
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
    summary="List all precomputed percentile buckets",
)
@limiter.limit("60/minute")
async def list_percentiles(
    request: Request,
    pool: asyncpg.Pool = Depends(get_db),
) -> list[dict]:
    return await percentiles.get_all_percentiles(pool)


@router.post(
    "/percentiles/lookup",
    response_model=PercentileLookupResponse,
    summary="Look up the percentile for a given score and dimension",
)
@limiter.limit("60/minute")
async def lookup_percentile(
    request: Request,
    payload: PercentileLookupRequest,
    pool: asyncpg.Pool = Depends(get_db),
) -> PercentileLookupResponse:
    percentile = await percentiles.get_percentile(pool, payload.dimension, payload.score)
    return PercentileLookupResponse(
        dimension=payload.dimension,
        score=payload.score,
        percentile=percentile,
    )


@router.get(
    "/weights",
    response_model=WeightsResponse,
    summary="Get current public vs real dataset blending weights",
    description=(
        "Returns the current weights used to blend the public NLR seed dataset "
        "with real operator submissions. Weights are recalculated automatically "
        "as a BackgroundTask after each new diagnostic submission."
    ),
)
@limiter.limit("60/minute")
async def get_weights(
    request: Request,
    pool: asyncpg.Pool = Depends(get_db),
) -> WeightsResponse:
    data = await get_current_weights(pool)
    return WeightsResponse(
        public_weight=data["public_weight"],
        real_weight=data["real_weight"],
        real_count=data["real_count"],
        updated_at=data["updated_at"],
    )