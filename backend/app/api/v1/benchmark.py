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
from fastapi import APIRouter, Depends

from app.deps import get_db, rate_limit_dependency
from app.models.schemas import (
    BenchmarkQuestion,
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
    dependencies=[Depends(rate_limit_dependency)],
)
async def list_questions(
    pool: asyncpg.Pool = Depends(get_db),
) -> list[BenchmarkQuestion]:
    """Devuelve las preguntas ACTIVAS del benchmark (v2: tabla `question`).

    El frontend consume esto para armar el formulario del test.
    """
    return await benchmark_engine.get_questions(pool)


@router.get(
    "/stats",
    summary="Get population statistics per dimension",
    description="Returns mean, standard deviation, and sample size per dimension "
                "from public dataset and real submissions.",
    dependencies=[Depends(rate_limit_dependency)],
)
async def get_stats(
    pool: asyncpg.Pool = Depends(get_db),
) -> list[dict]:
    """Estadísticas (media, desviación, n) por dimensión del pool fundido.

    v2: en vez de leer `benchmark_scores` (que no existe), hace un UNION de
    las 5 columnas fijas de `public_dataset` + `benchmark_result`.

    NOTA FUTURA: si el frontend quiere stats separadas público/real, habría
    que agregar un filtro source — hoy se mezclan ambas en un solo conjunto.
    """
    rows = await pool.fetch(
        """
        SELECT dim AS dimension,
               AVG(score)    AS mean,
               STDDEV(score) AS std_dev,
               COUNT(*)      AS sample_size
        FROM (
            SELECT 'visibility' AS dim, visibility_score      AS score FROM public_dataset
            UNION ALL SELECT 'friction', friction_score       FROM public_dataset
            UNION ALL SELECT 'latency', latency_score         FROM public_dataset
            UNION ALL SELECT 'quantification', quantification_score FROM public_dataset
            UNION ALL SELECT 'blockers', blockers_score       FROM public_dataset
            UNION ALL SELECT 'visibility', visibility_score   FROM benchmark_result
            UNION ALL SELECT 'friction', friction_score       FROM benchmark_result
            UNION ALL SELECT 'latency', latency_score         FROM benchmark_result
            UNION ALL SELECT 'quantification', quantification_score FROM benchmark_result
            UNION ALL SELECT 'blockers', blockers_score       FROM benchmark_result
        ) t
        WHERE score IS NOT NULL
        GROUP BY dim
        ORDER BY dim
        """
    )
    return [
        {
            "dimension": row["dimension"],
            "mean": round(float(row["mean"]), 2),
            "std_dev": round(float(row["std_dev"] or 0), 2),
            "sample_size": row["sample_size"],
        }
        for row in rows
    ]


@router.get(
    "/percentiles",
    summary="List percentile thresholds per dimension",
    dependencies=[Depends(rate_limit_dependency)],
)
async def list_percentiles(
    pool: asyncpg.Pool = Depends(get_db),
) -> dict[str, dict]:
    """Devuelve umbrales de percentil (P10..P99) por dimensión (en vuelo).

    NOTA FUTURA: con datos crecientes, este endpoint es candidato a cache
    porque recalcula el blend en cada llamada.
    """
    return await percentiles.get_all_percentiles(pool)


@router.post(
    "/percentiles/lookup",
    response_model=PercentileLookupResponse,
    summary="Look up the percentile for a given score and dimension",
    dependencies=[Depends(rate_limit_dependency)],
)
async def lookup_percentile(
    payload: PercentileLookupRequest,
    pool: asyncpg.Pool = Depends(get_db),
) -> PercentileLookupResponse:
    """Da el percentil de un score concreto dentro de una dimensión (en vuelo).

    payload.dimension es un Enum Dimension; lo pasamos como .value (str)
    porque percentiles.get_percentile() espera el nombre corto.
    """
    percentile = await percentiles.get_percentile(
        pool, payload.dimension.value, payload.score
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
    dependencies=[Depends(rate_limit_dependency)],
)
async def get_weights(
    pool: asyncpg.Pool = Depends(get_db),
) -> WeightsResponse:
    """Lee el estado vigente del rebalanceo (tabla single-row rebalance_config).

    Fallback: si aún no hubo respuesta real, devuelve 100% público.
    """
    data = await get_current_weights(pool)
    return WeightsResponse(
        public_weight=data["public_weight"],
        real_weight=data["real_weight"],
        real_count=data["real_count"],
        updated_at=data["updated_at"],
    )