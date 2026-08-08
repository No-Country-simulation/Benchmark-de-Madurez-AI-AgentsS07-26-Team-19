"""Diagnostic endpoints -- submit answers and retrieve results.

Flujo v2 (cómo viaja una respuesta por el sistema):
    1. POST /diagnostic  recibe answers [{question_id:int, value:1-5}]
    2. benchmark_engine.save_diagnostic()  crea benchmark_response +
       response_answer ×N + benchmark_result (todo en una transacción)
    3. El percentil se calcula EN VUELO mezclando public_dataset (público)
       con benchmark_result (real) — ver services/percentiles.py
    4. run_rebalancing() corre como BackgroundTask: actualiza la tabla
       single-row rebalance_config con los pesos públicos/real vigentes.

Idempotencia:
  - session_id actúa como Idempotency-Key (patrón Stripe). Una repetición con
    las mismas respuestas reproduce el resultado guardado; respuestas distintas
    bajo la misma sesión devuelven HTTP 409. El anonimato se mantiene vía el
    campo UNIQUE `anonymous_code` de benchmark_response.
"""

import asyncpg
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status

from app.core.security import RATE_LIMIT, generate_anon_session_id, limiter
from app.deps import get_db
from app.models.schemas import (
    DiagnosticFrictionProfile,
    DiagnosticResponseV2,
    DiagnosticResult,
    DiagnosticSubmitRequest,
    Dimension,
    DimensionScore,
    WeightsResponse,
)
from app.services import benchmark_engine, idempotency, percentiles, scoring
from app.services.idempotency import IdempotencyConflictError
from app.services.rebalancing import get_current_weights, run_rebalancing

router = APIRouter(prefix="/diagnostic", tags=["diagnostic"])


def _build_friction_profile(dimensions: list[DimensionScore]) -> DiagnosticFrictionProfile:
    """Identifica la dimensión con menor score (la "fricción" dominante).

    Es la dimensión donde el operador está más débil — el entregable de
    output personalizado del challenge. Devuelve el perfil cualitativo.

    NOTA futura: acá se podría subir a un servicio independiente cuando
    querramos agregar interpretaciones más ricas por dimensión.
    """
    weakest = min(dimensions, key=lambda d: d.score)
    return DiagnosticFrictionProfile(
        dominant_dimension=weakest.dimension.value,
        score=weakest.score,
        interpretation=(
            f"La dimensión con mayor fricción es {weakest.dimension.value} "
            f"con un score de {weakest.score:.1f}/100."
        ),
    )


def _is_top_quartile(dimension_scores: list[DimensionScore]) -> bool:
    """¿El overall del operador está en el cuartil superior (>= P75)?

    Se calcula con el promedio de los scores → si >= 75%, se muestra la
    bandera cuartil_superior = True en la respuesta.

    NOTA para futuro: si queremos usar los percentiles reales por dimensión
    en vez del promedio simple, el cálculo vive en services/percentiles.py.
    """
    overall = scoring.compute_overall_score(dimension_scores)
    return overall >= 75.0


@router.post(
    "",
    response_model=DiagnosticResponseV2,
    summary="Submit a diagnostic",
    description=(
        "Evalúa las respuestas, calcula scores por dimensión, percentiles en vuelo, "
        "perfil de fricción y rebalancea pesos como BackgroundTask. "
        "Idempotente: el mismo session_id con las mismas respuestas reproduce el "
        "resultado guardado; respuestas distintas devuelven HTTP 409."
    ),
)
@limiter.limit(RATE_LIMIT)
async def submit_diagnostic(
    request: Request,
    payload: DiagnosticSubmitRequest,
    background_tasks: BackgroundTasks,
    pool: asyncpg.Pool = Depends(get_db),
) -> DiagnosticResponseV2:
    """Procesa una encuesta completa: scoring + percentiles + perfil + persistencia.

    - session_id: si el frontend no lo manda, generamos uno anónimo.
    - answers: lista de {question_id:int, value:1-5}.
    - Dimensiones se agrupan vía benchmark_engine.get_questions().
    - Percentil: se calcula EN VUELO contra public_dataset + benchmark_result.
    - BackgroundTask: run_rebalancing() actualiza la config de pesos tras guardar.
    """
    # 1) Sesión anónima (o la que mande el frontend)
    session_id = payload.session_id or generate_anon_session_id()
    fingerprint = idempotency.compute_answers_fingerprint(payload.answers)

    # 2) Preguntas activas → mapa question_id(int) → Dimension
    questions = await benchmark_engine.get_questions(pool)
    question_dimensions = {q.id: q.dimension for q in questions}

    # 3) Score por dimensión (escala 0-100) via services/scoring.py
    dimension_scores = scoring.compute_dimension_scores(
        payload.answers, question_dimensions
    )

    # 4) Percentiles EN VUELO (mezcla público + real) por dimensión
    dimension_map = {ds.dimension.value: ds.score for ds in dimension_scores}
    percentiles_map = await percentiles.calculate_percentiles_for_user(pool, dimension_map)
    for ds in dimension_scores:
        ds.percentile = percentiles_map.get(ds.dimension.value, 50.0)

    # 5) Score total (promedio simple de dimensiones)
    overall = scoring.compute_overall_score(dimension_scores)
    overall_percentile = round(
        sum(ds.percentile or 0 for ds in dimension_scores) / max(len(dimension_scores), 1),
        2,
    )

    # 6) Persistir (o rejugar) benchmark_response + answer ×N + benchmark_result
    try:
        outcome = await benchmark_engine.save_diagnostic_idempotent(
            pool,
            session_id=session_id,
            fingerprint=fingerprint,
            answers=payload.answers,
            dimension_scores=dimension_scores,
            overall_score=overall,
            overall_percentile=overall_percentile,
        )
    except IdempotencyConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    # 7) Rebalancear solo para registros nuevos; los replays lo omiten
    if not outcome.replayed:
        background_tasks.add_task(run_rebalancing, pool)

    # 8) Armar la respuesta enriquecida
    result = DiagnosticResult(
        id=outcome.diagnostic_id,
        session_id=session_id,
        overall_score=overall,
        dimensions=dimension_scores,
        created_at=outcome.created_at,
    )

    friction = _build_friction_profile(dimension_scores)
    is_top = _is_top_quartile(dimension_scores)
    weights = await get_current_weights(pool)

    message = (
        "Diagnostic replayed from session"
        if outcome.replayed
        else "Diagnostic submitted successfully"
    )

    return DiagnosticResponseV2(
        diagnostic=result,
        perfil_friccion=friction,
        cuartil_superior=is_top,
        pesos=WeightsResponse(
            public_weight=weights["public_weight"],
            real_weight=weights["real_weight"],
            real_count=weights["real_count"],
            updated_at=weights["updated_at"],
        ),
        message=message,
    )


@router.get(
    "/{diagnostic_id}",
    response_model=DiagnosticResult,
    summary="Get diagnostic result by id",
)
@limiter.limit(RATE_LIMIT)
async def get_diagnostic(
    request: Request,
    diagnostic_id: int,
    pool: asyncpg.Pool = Depends(get_db),
) -> DiagnosticResult:
    """Obtiene un diagnóstico ya guardado por su id (SERIAL).

    Arma el DiagnosticResult desde el JOIN benchmark_response +
    benchmark_result (get_diagnostic_by_id en benchmark_engine.py).
    """
    row = await benchmark_engine.get_diagnostic_by_id(pool, diagnostic_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnostic not found",
        )

    # Mapeo fijo: columna de BD (sufijo _score) → Dimension corta
    col_to_dim = {
        "visibility_score": "visibility",
        "friction_score": "friction",
        "latency_score": "latency",
        "quantification_score": "quantification",
        "blockers_score": "blockers",
    }
    dimensions = [
        DimensionScore(
            dimension=Dimension(dim_name),  # str → enum Dimension
            score=float(row[column] or 0.0),
            percentile=50.0,  # NOTA FUTURA: v2 no guarda percentile por fila; se recalcula en vuelo
        )
        for column, dim_name in col_to_dim.items()
    ]

    return DiagnosticResult(
        id=row["id"],
        session_id=row["anonymous_code"],
        overall_score=float(row["overall_score"]),
        dimensions=dimensions,
        created_at=row["created_at"],
    )