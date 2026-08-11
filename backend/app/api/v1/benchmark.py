"""Benchmark endpoints -- questions, stats, percentile lookup, and weights.

Todos los endpoints de este router leen del esquema v2:
    - `question` para las preguntas activas.
    - `public_dataset` y `benchmark_result` para las estadísticas y
      percentiles (mezclados público + real).
    - `rebalance_config` (single-row) para los pesos vigentes.

NOTA FUTURA: el cálculo de stats/percentiles está EN VUELO, así que con
poblaciones grandes convendría revisitar si se necesita cache. Por ahora,
20 filas públicas es trivial.
"""

import asyncpg
from fastapi import APIRouter, Request

from app.core.cache import ttl_cache
from app.core.dimensions import DIMENSION_SCORE_COLUMN, NAME_TO_DIMENSION
from app.core.security import RATE_LIMIT, limiter
from app.deps import DbPool
from app.models.schemas import (
    BenchmarkQuestion,
    BenchmarkStats,
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
@limiter.limit(RATE_LIMIT)
async def list_questions(
    request: Request,
    pool: DbPool,
) -> list[BenchmarkQuestion]:
    """Devuelve las preguntas ACTIVAS del benchmark (v2: tabla `question`).

    El frontend consume esto para armar el formulario del test.
    """
    return await benchmark_engine.get_questions(pool)


@ttl_cache(seconds=30)
async def _fetch_dimension_stats(pool: asyncpg.Pool) -> list[asyncpg.Record]:
    """UNION de las 5 columnas fijas de public_dataset + benchmark_result.

    Cacheado 30s: no depende de ningun parametro de request, asi que es el
    endpoint mas facil de golpear con volumen para forzar trabajo en la DB.
    """
    select_blocks = []
    for dimension, column in DIMENSION_SCORE_COLUMN.items():
        select_blocks.append(
            f"SELECT '{dimension.value}' AS dim, {column} AS score FROM public_dataset"
        )
        select_blocks.append(
            f"SELECT '{dimension.value}' AS dim, {column} AS score FROM benchmark_result"
        )
    union_sql = "\nUNION ALL\n".join(select_blocks)

    return await pool.fetch(
        f"""
        SELECT dim AS dimension,
               AVG(score)    AS mean,
               STDDEV(score) AS std_dev,
               COUNT(*)      AS sample_size
        FROM ({union_sql}) t
        WHERE score IS NOT NULL
        GROUP BY dim
        ORDER BY dim
        """
    )


@router.get(
    "/stats",
    response_model=list[BenchmarkStats],
    summary="Get population statistics per dimension",
    description="Returns mean, standard deviation, and sample size per dimension "
    "from public dataset and real submissions.",
)
@limiter.limit(RATE_LIMIT)
async def get_stats(
    request: Request,
    pool: DbPool,
) -> list[BenchmarkStats]:
    """Estadísticas (media, desviación, n) por dimensión del pool fundido.

    NOTA FUTURA: si el frontend quiere stats separadas público/real, habría
    que agregar un filtro source — hoy se mezclan ambas en un solo conjunto.
    """
    rows = await _fetch_dimension_stats(pool)
    return [
        BenchmarkStats(
            dimension=NAME_TO_DIMENSION[row["dimension"]],
            mean=round(float(row["mean"]), 2),
            std_dev=round(float(row["std_dev"] or 0), 2),
            sample_size=row["sample_size"],
        )
        for row in rows
    ]


@router.get(
    "/percentiles",
    summary="List percentile thresholds per dimension",
)
@limiter.limit(RATE_LIMIT)
async def list_percentiles(
    request: Request,
    pool: DbPool,
) -> dict[str, dict[float, float]]:
    """Devuelve umbrales de percentil (P10..P99) por dimensión (en vuelo).

    Usa los pesos VIGENTES del rebalanceo para el blend público + real, así
    el resultado es consistente con `/weights` y con `/diagnostic`.

    NOTA FUTURA: con datos crecientes, este endpoint es candidato a cache
    porque recalcula el blend en cada llamada.
    """
    weights = await get_current_weights(pool)
    return await percentiles.get_all_percentiles(
        pool, weights.public_weight, weights.real_weight
    )


@router.post(
    "/percentiles/lookup",
    response_model=PercentileLookupResponse,
    summary="Look up the percentile for a given score and dimension",
)
@limiter.limit(RATE_LIMIT)
async def lookup_percentile(
    request: Request,
    payload: PercentileLookupRequest,
    pool: DbPool,
) -> PercentileLookupResponse:
    """Da el percentil de un score concreto dentro de una dimensión (en vuelo)."""
    weights = await get_current_weights(pool)
    percentile = await percentiles.get_percentile(
        pool,
        payload.dimension,
        payload.score,
        weights.public_weight,
        weights.real_weight,
    )
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
@limiter.limit(RATE_LIMIT)
async def get_weights(
    request: Request,
    pool: DbPool,
) -> WeightsResponse:
    """Lee el estado vigente del rebalanceo (tabla single-row rebalance_config).

    Fallback: si aún no hubo respuesta real, devuelve 100% público.
    """
    data = await get_current_weights(pool)
    return WeightsResponse.from_state(data)