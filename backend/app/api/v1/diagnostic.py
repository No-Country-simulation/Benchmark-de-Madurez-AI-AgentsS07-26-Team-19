from datetime import datetime, timezone
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import generate_anon_session_id
from app.deps import get_db, rate_limit_dependency
from app.models.schemas import (
    DiagnosticResponse,
    DiagnosticResult,
    DiagnosticSubmitRequest,
    DimensionScore,
)
from app.services import benchmark_engine, percentiles, scoring

router = APIRouter(prefix="/diagnostic", tags=["diagnostic"])


@router.post(
    "",
    response_model=DiagnosticResponse,
    dependencies=[Depends(rate_limit_dependency)],
)
async def submit_diagnostic(
    payload: DiagnosticSubmitRequest,
    pool: asyncpg.Pool = Depends(get_db),
) -> DiagnosticResponse:
    session_id = payload.session_id or generate_anon_session_id()

    questions = await benchmark_engine.get_questions(pool)
    question_dimensions = {q.id: q.dimension for q in questions}

    dimension_scores = scoring.compute_dimension_scores(
        payload.answers, question_dimensions
    )

    for ds in dimension_scores:
        ds.percentile = await percentiles.get_percentile(pool, ds.dimension, ds.score)

    overall = scoring.compute_overall_score(dimension_scores)

    answers_data = [a.model_dump() for a in payload.answers]
    dimension_data = {ds.dimension.value: ds.model_dump() for ds in dimension_scores}

    diagnostic_id = await benchmark_engine.save_diagnostic(
        pool,
        session_id=session_id,
        overall_score=overall,
        dimension_scores=dimension_data,
        answers=answers_data,
    )

    result = DiagnosticResult(
        id=diagnostic_id,
        session_id=session_id,
        overall_score=overall,
        dimensions=dimension_scores,
        created_at=datetime.now(timezone.utc),
    )

    return DiagnosticResponse(diagnostic=result)


@router.get(
    "/{diagnostic_id}",
    response_model=DiagnosticResult,
    dependencies=[Depends(rate_limit_dependency)],
)
async def get_diagnostic(
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
        DimensionScore(**v) for v in row["dimension_scores"].values()
    ]

    return DiagnosticResult(
        id=row["id"],
        session_id=row["session_id"],
        overall_score=float(row["overall_score"]),
        dimensions=dimensions,
        created_at=row["created_at"],
    )
