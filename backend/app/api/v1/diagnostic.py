"""Diagnostic endpoint -- submit answers and receive benchmark results.

Design notes:
  - Thin controller: all business logic lives in the service layer.
  - BackgroundTask pattern: rebalancing runs after the response is sent
    so it does not add latency to the request. See:
    https://fastapi.tiangolo.com/tutorial/background-tasks/
  - Facade pattern: _build_friction_profile() consolidates multi-dimension
    data into a single qualitative output without exposing scoring internals.
  - Idempotency pattern: session_id acts as the Idempotency-Key. A repeated
    submission with the same answers replays the stored result; different
    answers under the same session conflict (HTTP 409). Concurrency is
    serialized with pg_advisory_xact_lock, so simultaneous duplicates cannot
    create two rows. See:
    https://docs.stripe.com/api/idempotent_requests
    https://www.postgresql.org/docs/current/functions-admin.html
"""

import json
from uuid import UUID

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


def _build_friction_profile(dimension_scores: list[DimensionScore]) -> DiagnosticFrictionProfile:
    """Identify the lowest-scoring dimension as the dominant friction point.

    Uses the Facade pattern to convert raw dimension scores into a
    single human-readable interpretation without exposing scoring internals.
    """
    if not dimension_scores:
        return DiagnosticFrictionProfile(
            dominant_dimension="unknown",
            score=0.0,
            interpretation="No dimension scores available.",
        )

    worst = min(dimension_scores, key=lambda ds: ds.score)

    interpretations: dict[Dimension, str] = {
        Dimension.VISIBILIDAD_CROSS_LAYER: (
            "Cross-layer visibility is the main friction point. "
            "The facility lacks a unified real-time view across IT, cooling, and power layers."
        ),
        Dimension.ATRIBUCION_FRICCION: (
            "Friction attribution is the primary gap. "
            "The team cannot pinpoint which physical interface causes the most stranded capacity."
        ),
        Dimension.LATENCIA_COORDINACION: (
            "Coordination latency is the bottleneck. "
            "Cooling and power do not respond fast enough when workload changes."
        ),
        Dimension.AUTO_CUANTIFICACION: (
            "Self-quantification is the weak point. "
            "The facility does not have reliable data on how much stranded capacity it carries."
        ),
        Dimension.BLOQUEANTES: (
            "Operational blockers are the primary issue. "
            "Even when the root cause is known, organizational or technical barriers prevent resolution."
        ),
    }

    return DiagnosticFrictionProfile(
        dominant_dimension=worst.dimension.value,
        score=worst.score,
        interpretation=interpretations.get(worst.dimension, f"{worst.dimension.value} scored lowest."),
    )


@router.post(
    "",
    response_model=DiagnosticResponseV2,
    summary="Submit a benchmark diagnostic",
    description=(
        "Receives operator answers, computes dimension scores and percentiles against "
        "the benchmark population, persists the diagnostic, and triggers a background "
        "rebalancing task to update public/real dataset weights. "
        "Idempotent: the same session_id with the same answers replays the stored "
        "result; the same session_id with different answers returns 409."
    ),
)
@limiter.limit(RATE_LIMIT)
async def submit_diagnostic(
    request: Request,
    payload: DiagnosticSubmitRequest,
    background_tasks: BackgroundTasks,
    pool: asyncpg.Pool = Depends(get_db),
) -> DiagnosticResponseV2:
    session_id = payload.session_id or generate_anon_session_id()
    fingerprint = idempotency.compute_answers_fingerprint(payload.answers)

    questions = await benchmark_engine.get_questions(pool)
    question_dimensions = {q.id: q.dimension for q in questions}

    dimension_scores = scoring.compute_dimension_scores(payload.answers, question_dimensions)

    for ds in dimension_scores:
        ds.percentile = await percentiles.get_percentile(pool, ds.dimension, ds.score)

    overall = scoring.compute_overall_score(dimension_scores)

    answers_data = [a.model_dump() for a in payload.answers]
    dimension_data = {ds.dimension.value: ds.model_dump() for ds in dimension_scores}

    try:
        outcome = await benchmark_engine.save_diagnostic_idempotent(
            pool,
            session_id=session_id,
            fingerprint=fingerprint,
            overall_score=overall,
            dimension_scores=dimension_data,
            answers=answers_data,
        )
    except IdempotencyConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    # Rebalancing only runs for newly-created diagnostics; replays skip it.
    if not outcome.replayed:
        background_tasks.add_task(run_rebalancing, pool)

    result = DiagnosticResult(
        id=outcome.diagnostic_id,
        session_id=session_id,
        overall_score=overall,
        dimensions=dimension_scores,
        created_at=outcome.created_at,
    )

    friction_profile = _build_friction_profile(dimension_scores)
    cuartil_superior = overall >= 75.0

    weights_data = await get_current_weights(pool)
    pesos = WeightsResponse(
        public_weight=weights_data["public_weight"],
        real_weight=weights_data["real_weight"],
        real_count=weights_data["real_count"],
        updated_at=weights_data["updated_at"],
    )

    message = (
        "Diagnostic replayed from session"
        if outcome.replayed
        else "Diagnostic submitted successfully"
    )

    return DiagnosticResponseV2(
        diagnostic=result,
        perfil_friccion=friction_profile,
        cuartil_superior=cuartil_superior,
        pesos=pesos,
        message=message,
    )


@router.get(
    "/{diagnostic_id}",
    response_model=DiagnosticResult,
    summary="Retrieve a saved diagnostic by ID",
)
@limiter.limit(RATE_LIMIT)
async def get_diagnostic(
    request: Request,
    diagnostic_id: UUID,
    pool: asyncpg.Pool = Depends(get_db),
) -> DiagnosticResult:
    row = await benchmark_engine.get_diagnostic_by_id(pool, diagnostic_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnostic not found",
        )

    dimensions = [
        DimensionScore(**v) for v in json.loads(row["dimension_scores"]).values()
    ]

    return DiagnosticResult(
        id=row["id"],
        session_id=row["session_id"],
        overall_score=float(row["overall_score"]),
        dimensions=dimensions,
        created_at=row["created_at"],
    )
