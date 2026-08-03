"""Benchmark engine -- orchestrates question retrieval and diagnostic flow.

This module follows a Repository-like pattern: the service owns all database
access and transactional rules, while the API controller stays thin.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import asyncpg

from app.models.schemas import BenchmarkQuestion, Dimension
from app.services.idempotency import (
    IdempotencyConflictError,
    compute_answers_fingerprint,
)


@dataclass(frozen=True)
class DiagnosticOutcome:
    """Result of an idempotent diagnostic submission.

    Attributes:
        diagnostic_id: UUID of the stored (or replayed) diagnostic.
        created_at: Timestamp of the diagnostic record.
        replayed: True if an existing diagnostic was replayed, False if a new
            one was inserted.
    """

    diagnostic_id: UUID
    created_at: datetime
    replayed: bool


async def get_questions(pool: asyncpg.Pool) -> list[BenchmarkQuestion]:
    rows = await pool.fetch(
        """
        SELECT id, dimension, text, display_order
        FROM benchmark_questions
        ORDER BY display_order ASC
        """
    )
    return [
        BenchmarkQuestion(
            id=row["id"],
            dimension=Dimension(row["dimension"]),
            text=row["text"],
            order=row["display_order"],
        )
        for row in rows
    ]


async def get_diagnostic_by_id(
    pool: asyncpg.Pool, diagnostic_id: UUID
) -> asyncpg.Record | None:
    return await pool.fetchrow(
        """
        SELECT id, session_id, overall_score, dimension_scores, created_at
        FROM diagnostics
        WHERE id = $1
        """,
        diagnostic_id,
    )


async def get_diagnostic_by_session(
    conn: asyncpg.Connection, session_id: str
) -> asyncpg.Record | None:
    """Return the most recent diagnostic for a session, if any.

    Used by the idempotency guard: a repeated submission under the same
    session replays the stored result instead of inserting a duplicate.
    """
    return await conn.fetchrow(
        """
        SELECT id, session_id, overall_score, dimension_scores, answers, created_at
        FROM diagnostics
        WHERE session_id = $1
        ORDER BY created_at DESC
        LIMIT 1
        """,
        session_id,
    )


async def save_diagnostic(
    conn: asyncpg.Connection,
    session_id: str,
    overall_score: float,
    dimension_scores: dict[str, dict[str, Any]],
    answers: list[dict[str, Any]],
) -> UUID:
    """Insert a diagnostic inside an existing transaction."""
    row = await conn.fetchrow(
        """
        INSERT INTO diagnostics (session_id, overall_score, dimension_scores, answers)
        VALUES ($1, $2, $3::jsonb, $4::jsonb)
        RETURNING id
        """,
        session_id,
        overall_score,
        dimension_scores,
        answers,
    )
    return UUID(str(row["id"]))


async def save_diagnostic_idempotent(
    pool: asyncpg.Pool,
    session_id: str,
    fingerprint: str,
    overall_score: float,
    dimension_scores: dict[str, dict[str, Any]],
    answers: list[dict[str, Any]],
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
                overall_score=overall_score,
                dimension_scores=dimension_scores,
                answers=answers,
            )
            return DiagnosticOutcome(
                diagnostic_id=diagnostic_id,
                created_at=datetime.now(UTC),
                replayed=False,
            )
