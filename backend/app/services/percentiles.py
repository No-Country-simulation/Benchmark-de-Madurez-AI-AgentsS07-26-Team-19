"""Percentile calculation against benchmark population."""

import asyncpg

from app.models.schemas import Dimension


async def get_percentile(
    pool: asyncpg.Pool,
    dimension: Dimension,
    score: float,
) -> float:
    """Return percentile (0–100) for a score within a dimension."""
    row = await pool.fetchrow(
        """
        SELECT percentile
        FROM benchmark_percentiles
        WHERE dimension = $1
          AND score_bucket <= $2
        ORDER BY score_bucket DESC
        LIMIT 1
        """,
        dimension.value,
        score,
    )
    if row:
        return float(row["percentile"])

    # Fallback: compute from raw scores if percentile table is empty
    stats = await pool.fetchrow(
        """
        SELECT COUNT(*) AS total,
               COUNT(*) FILTER (WHERE score <= $2) AS below
        FROM benchmark_scores
        WHERE dimension = $1
        """,
        dimension.value,
        score,
    )
    if stats and stats["total"] > 0:
        return round((stats["below"] / stats["total"]) * 100, 2)
    return 50.0


async def get_all_percentiles(
    pool: asyncpg.Pool,
) -> list[dict]:
    rows = await pool.fetch(
        """
        SELECT dimension, score_bucket, percentile
        FROM benchmark_percentiles
        ORDER BY dimension, score_bucket
        """
    )
    return [dict(row) for row in rows]
