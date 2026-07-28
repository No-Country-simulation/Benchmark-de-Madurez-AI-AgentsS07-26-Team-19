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


async def save_diagnostic(
    pool: asyncpg.Pool,
    session_id: str,
    overall_score: float,
    dimension_scores: dict,
    answers: list[dict],
) -> UUID:
    row = await pool.fetchrow(
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
