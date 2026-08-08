"""Benchmark engine — orchestrates question retrieval and diagnostic flow."""

from uuid import UUID

import asyncpg

from app.models.schemas import (
    BenchmarkQuestion,
    DiagnosticAnswer,
    Dimension,
    DimensionScore,
)


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
            id=row["id"],               # ahora int
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


async def save_diagnostic(
    pool: asyncpg.Pool,
    session_id: str,
    answers: list[DiagnosticAnswer],
    dimension_scores: list[DimensionScore],
    overall_score: float,
    overall_percentile: float,
) -> int:
    async with pool.acquire() as conn:
        async with conn.transaction():
            # 1) Crea la encuesta (benchmark_response)
            response_id = await conn.fetchval(
                """
                INSERT INTO benchmark_response (anonymous_code, completed_at)
                VALUES ($1, NOW())
                RETURNING id
                """,
                session_id,
            )

            # 2) Inserta cada respuesta (response_answer) con su score
            for answer in answers:
                await conn.execute(
                    """
                    INSERT INTO response_answer (response_id, question_id, answer, score)
                    VALUES ($1, $2, $3, $4)
                    """,
                    response_id,
                    answer.question_id,
                    str(answer.value),
                    (answer.value / 5) * 100,
                )

            # 3) Guarda el resultado (benchmark_result)
            scores_map = {ds.dimension.value: ds.score for ds in dimension_scores}
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
                scores_map.get("visibility", 0.00),
                scores_map.get("friction", 0.00),
                scores_map.get("latency", 0.00),
                scores_map.get("quantification", 0.00),
                scores_map.get("blockers", 0.00),
                overall_score,
                overall_percentile,
            )
    return response_id
