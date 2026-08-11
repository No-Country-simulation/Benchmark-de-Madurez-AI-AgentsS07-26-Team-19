"""Benchmark engine -- orchestrates question retrieval and diagnostic flow.

This module follows a Repository-like pattern: the service owns all database
access and transactional rules, while the API controller stays thin.

The engine works against the v2 schema:
    - `question`               → active benchmark questions.
    - `benchmark_response`     → one row per completed session
      (anonymous_code field acts as the natural idempotency key).
    - `response_answer`        → one row per question answered, with its
      normalized per-question score (0-100).
    - `benchmark_result`       → per-dimension scores, overall score and
      overall percentile for each response.

Idempotency: `session_id` is treated as an Idempotency-Key. A repeated
submission with the same answers under the same session replays the stored
result; different answers under the same session raise an
IdempotencyConflictError. Concurrency is serialized with a PostgreSQL
transaction-scoped advisory lock.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast

import asyncpg

from app.core.dimensions import DIMENSION_SCORE_COLUMN, normalize_answer
from app.models.schemas import (
    BenchmarkQuestion,
    DiagnosticAnswer,
    Dimension,
    DimensionScore,
)
from app.services.idempotency import (
    IdempotencyConflictError,
    compute_answers_fingerprint,
)


@dataclass(frozen=True)
class DiagnosticOutcome:
    """Result of an idempotent diagnostic submission.

    Attributes:
        diagnostic_id: id of the stored (or replayed) benchmark_response.
        created_at: Timestamp of the diagnostic record.
        replayed: True if an existing diagnostic was replayed, False if a new
            one was inserted.
    """

    diagnostic_id: int
    created_at: datetime
    replayed: bool


async def get_questions(pool: asyncpg.Pool) -> list[BenchmarkQuestion]:
    rows = await pool.fetch(
        """
        SELECT id, dimension, question AS text, order_index AS order
        FROM question
        WHERE is_active = TRUE
        ORDER BY order_index ASC
        """
    )
    return [
        BenchmarkQuestion(
            id=row["id"],  # ahora int
            dimension=Dimension(row["dimension"]),
            text=row["text"],
            order=row["order"],
        )
        for row in rows
    ]


async def get_diagnostic_by_id(
    pool: asyncpg.Pool, diagnostic_id: int
) -> asyncpg.Record | None:
    return await pool.fetchrow(
        """
        SELECT r.id, r.anonymous_code, br.overall_score, br.overall_percentile,
               br.visibility_score, br.friction_score, br.latency_score,
               br.quantification_score, br.blockers_score,
               r.created_at, r.completed_at
        FROM benchmark_response r
        LEFT JOIN benchmark_result br ON br.response_id = r.id
        WHERE r.id = $1
        """,
        diagnostic_id,
    )


async def get_diagnostic_by_session(
    conn: asyncpg.Connection, session_id: str
) -> dict[str, Any] | None:
    """Return the most recent diagnostic for a session, if any.

    Used by the idempotency guard: a repeated submission under the same
    session replays the stored result instead of inserting a duplicate.
    The stored answers are rebuilt from `response_answer` so the fingerprint
    can be compared against the incoming submission.
    """
    response = await conn.fetchrow(
        """
        SELECT id, created_at
        FROM benchmark_response
        WHERE anonymous_code = $1
        ORDER BY created_at DESC
        LIMIT 1
        """,
        session_id,
    )
    if response is None:
        return None

    answers = await conn.fetch(
        """
        SELECT question_id, answer
        FROM response_answer
        WHERE response_id = $1
        ORDER BY question_id
        """,
        response["id"],
    )
    return {
        "id": response["id"],
        "answers": [
            {"question_id": row["question_id"], "value": int(row["answer"])}
            for row in answers
            if row["answer"] is not None
        ],
        "created_at": response["created_at"],
    }


async def save_diagnostic(
    conn: asyncpg.Connection,
    session_id: str,
    answers: list[DiagnosticAnswer],
    dimension_scores: list[DimensionScore],
    overall_score: float,
    overall_percentile: float,
) -> int:
    """Insert a new diagnostic inside an existing transaction (v2 schema).

    Steps: benchmark_response → response_answer × N → benchmark_result.
    """
    # 1) Crea la encuesta (benchmark_response); anonymous_code = session_id
    response_id = await conn.fetchval(
        """
        INSERT INTO benchmark_response (anonymous_code, completed_at)
        VALUES ($1, NOW())
        RETURNING id
        """,
        session_id,
    )

    # 2) Inserta cada respuesta (response_answer) con su score normalizado
    for answer in answers:
        await conn.execute(
            """
            INSERT INTO response_answer (response_id, question_id, answer, score)
            VALUES ($1, $2, $3, $4)
            """,
            response_id,
            answer.question_id,
            str(answer.value),
            normalize_answer(answer.value),
        )

    # 3) Guarda el resultado (benchmark_result) — columnas derivadas del
    #    mapeo unico de dimensiones (app/core/dimensions.py)
    scores_map = {ds.dimension: ds.score for ds in dimension_scores}
    dim_scores = [scores_map.get(dim, 0.00) for dim in DIMENSION_SCORE_COLUMN]
    await conn.execute(
        """
        INSERT INTO benchmark_result (
            response_id, visibility_score, friction_score,
            latency_score, quantification_score, blockers_score,
            overall_score, overall_percentile
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """,
        response_id,
        *dim_scores,
        overall_score,
        overall_percentile,
    )
    return cast(int, response_id)


async def save_diagnostic_idempotent(
    pool: asyncpg.Pool,
    session_id: str,
    fingerprint: str,
    answers: list[DiagnosticAnswer],
    dimension_scores: list[DimensionScore],
    overall_score: float,
    overall_percentile: float,
) -> DiagnosticOutcome:
    """Persist or replay a diagnostic keyed by session_id.

    A PostgreSQL xact-scoped advisory lock serializes concurrent submissions
    for the same session. If the session already has a diagnostic with the same
    answer fingerprint, the stored record is replayed (no new row is inserted
    and no side effects are triggered). If the answers differ, an
    IdempotencyConflictError is raised. Otherwise a new diagnostic is inserted.

    Important: percentiles are not part of the stored record used for replay;
    callers recompute percentiles against the current benchmark population, so a
    replayed response may reflect newer percentile values.
    """
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Serialize concurrent submissions for the same session. The lock is
            # released automatically on commit/rollback (xact-scoped).
            await conn.execute(
                "SELECT pg_advisory_xact_lock(hashtext($1))",
                f"diag:{session_id}",
            )

            existing = await get_diagnostic_by_session(conn, session_id)

            if existing is not None:
                stored_fingerprint = compute_answers_fingerprint(existing["answers"])
                if stored_fingerprint != fingerprint:
                    raise IdempotencyConflictError(
                        "Session already has a diagnostic with different answers. "
                        "Use a new session_id to submit a new diagnostic."
                    )
                return DiagnosticOutcome(
                    diagnostic_id=existing["id"],
                    created_at=existing["created_at"],
                    replayed=True,
                )

            diagnostic_id = await save_diagnostic(
                conn,
                session_id=session_id,
                answers=answers,
                dimension_scores=dimension_scores,
                overall_score=overall_score,
                overall_percentile=overall_percentile,
            )
            return DiagnosticOutcome(
                diagnostic_id=diagnostic_id,
                created_at=datetime.now(UTC),
                replayed=False,
            )


async def update_ai_analysis(
    pool: asyncpg.Pool,
    response_id: int,
    ai_analysis: str,
) -> None:
    """Persiste el análisis IA en ``benchmark_result.ai_analysis``.

    Corre como BackgroundTask tras el diagnóstico para no bloquear la
    respuesta del POST; es idempotente (UPDATE por response_id).
    """
    await pool.execute(
        """
        UPDATE benchmark_result
        SET ai_analysis = $2
        WHERE response_id = $1
        """,
        response_id,
        ai_analysis,
    )