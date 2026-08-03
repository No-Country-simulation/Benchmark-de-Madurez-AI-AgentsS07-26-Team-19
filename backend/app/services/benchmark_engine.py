"""Benchmark engine — orchestrates question retrieval and diagnostic flow."""

from uuid import UUID

import asyncpg

from app.models.schemas import BenchmarkQuestion, Dimension


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
    dimension_scores: dict,
    answers: list[dict],
) -> UUID:
    """Insert a diagnostic inside an existing transaction (advisory-lock held by caller)."""
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
    return row["id"]
