"""Percentile calculation against benchmark population."""

import asyncpg
import random
import math

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

def weighted_merge(
        public_scores: list[float],
        real_scores: list[float],
        public_weight: float,
        real_weight: float,
) -> list[float]:
    """Combine two score datasets using weighted sampling."""
    #how many elements to take from each dataset
    n_public = int(len(public_scores) * public_weight)
    n_real = int(len(real_scores) * real_weight)

    #randomly sample without replacement
    sampled_public = random.sample(public_scores, min(n_public, len(public_scores)))
    sampled_real = random.sample(real_scores, min(n_real, len(real_scores)))

    #combine and return
    return sampled_public + sampled_real

def calculate_percentile(
        user_score: float, # operator score
        combined_dataset: list[float], #dataset mixed from public and real scores
) -> float:
    """Calculate the percentile of a user score within a combined dataset.
        Formula: (count of values below user_score) / total_values × 100
        If the dataset is empty, returns 50.0 (neutral)."""
    if not combined_dataset:
        return 50.0
    
    all_scores = combined_dataset + [user_score]
    all_scores.sort()

    below = sum(1 for s in  all_scores if s < user_score) 
    percentile = (below / len(all_scores)) * 100

    return round(percentile, 1)

async def calculate_percentiles_for_user(
    pool: asyncpg.Pool,
    dimension_scores: dict[str, float],
    public_weight: float = 0.7,
    real_weight: float = 0.3,
) -> dict[str, float]:
    """
    Calculate percentiles for all dimensions by merging public and real datasets.
    
    For each dimension:
    1. Fetch public scores from benchmark_scores table
    2. Fetch real scores from diagnostics table (JSONB)
    3. Mix them using weighted_merge()
    4. Calculate the user's percentile with calculate_percentile()
    """
    dimensions = [dim.value for dim in Dimension]
    percentiles: dict[str, float] = {}

    for dim in dimensions:
        # 1. Fetch public scores for this dimension
        public_rows = await pool.fetch(
            """
            SELECT score FROM benchmark_scores
            WHERE dimension = $1
            """,
            dim,
        )
        public_scores = [float(row["score"]) for row in public_rows]

        # 2. Fetch real scores from existing diagnostics
        real_rows = await pool.fetch(
            """
            SELECT (dimension_scores->>$1)::float AS score
            FROM diagnostics
            WHERE dimension_scores ? $1
            """,
            dim,
        )
        real_scores = [float(row["score"]) for row in real_rows]

        # 3. Merge datasets using weighted sampling
        merged = weighted_merge(public_scores, real_scores, public_weight, real_weight)

        # 4. Calculate user's percentile
        user_score = dimension_scores.get(dim, 0.0)
        percentiles[dim] = calculate_percentile(user_score, merged)

    return percentiles

def compute_percentile_thresholds(
    scores: list[float],
    percentiles: list[float] = None,
) -> dict[float, float]:
    """
    Given a list of scores, compute the score threshold for each requested percentile.
    
    Returns: {10.0: 23.5, 25.0: 35.2, 50.0: 50.0, 75.0: 68.1, 90.0: 82.3, 99.0: 95.7}
    """
    if percentiles is None:
        percentiles = [10, 25, 50, 75, 90, 99]
    
    if not scores:
        return {p: 0.0 for p in percentiles}
    
    sorted_scores = sorted(scores)
    n = len(sorted_scores)
    thresholds = {}
    
    for p in percentiles:
        # Index position for this percentile
        index = int(math.ceil(p / 100 * n)) - 1
        index = max(0, min(index, n - 1))  # Clamp to valid range
        thresholds[p] = round(sorted_scores[index], 1)
    
    return thresholds

async def refresh_percentile_cache(
    pool: asyncpg.Pool,
    public_weight: float = 0.7,
    real_weight: float = 0.3,
) -> dict[str, dict[float, float]]:
    """
    Recalculate and store percentile thresholds for all dimensions.
    
    Returns the computed thresholds for each dimension.
    This function is meant to run periodically (e.g., via cron or after N new diagnostics).
    """
    dimensions = [dim.value for dim in Dimension]
    all_thresholds: dict[str, dict[float, float]] = {}

    for dim in dimensions:
        # 1. Fetch all public scores
        public_rows = await pool.fetch(
            "SELECT score FROM benchmark_scores WHERE dimension = $1", dim
        )
        public_scores = [float(row["score"]) for row in public_rows]

        # 2. Fetch all real scores
        real_rows = await pool.fetch(
            """
            SELECT (dimension_scores->>$1)::float AS score
            FROM diagnostics WHERE dimension_scores ? $1
            """,
            dim,
        )
        real_scores = [float(row["score"]) for row in real_rows]

        # 3. Merge datasets
        merged = weighted_merge(public_scores, real_scores, public_weight, real_weight)

        # 4. Compute thresholds
        thresholds = compute_percentile_thresholds(merged)
        all_thresholds[dim] = thresholds

        # 5. Store in DB (delete old, insert new)
        async with pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM benchmark_percentiles WHERE dimension = $1", dim
            )
            for percentile, score in thresholds.items():
                await conn.execute(
                    """
                    INSERT INTO benchmark_percentiles (dimension, score_bucket, percentile)
                    VALUES ($1, $2, $3)
                    """,
                    dim,
                    score,
                    percentile,
                )
    return all_thresholds

async def get_cached_percentile(
    pool: asyncpg.Pool,
    dimension: str,
    user_score: float,
) -> float:
    """
    Get the user's percentile from the cached thresholds.
    Much faster than recalculating from raw data every time.
    """
    row = await pool.fetchrow(
        """
        SELECT percentile FROM benchmark_percentiles
        WHERE dimension = $1 AND score_bucket <= $2
        ORDER BY score_bucket DESC LIMIT 1
        """,
        dimension,
        user_score,
    )
    return float(row["percentile"]) if row else 50.0