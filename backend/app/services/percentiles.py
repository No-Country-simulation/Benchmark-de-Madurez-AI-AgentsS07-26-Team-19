"""Percentile calculation against the blended public + real population.

The percentile is computed ON THE FLY (en vuelo): for each request we merge
the public reference dataset (public_dataset) with the real submissions
(benchmark_result) using weighted sampling, then compute where the user's
score falls. No precomputed cache table is used.

Design:
    - weighted_merge(): pure function, blends two score lists by weight.
    - calculate_percentile(): pure function, rank of a score in a list.
    - _load_blendedscores(): shared DB orchestration (no more duplication).
    - calculate_percentiles_for_user(): DB orchestration per dimension.
"""

import math
import random

import asyncpg

from app.core.dimensions import DIMENSION_SCORE_COLUMN
from app.models.schemas import Dimension

# ---------------------------------------------------------------------------
# Pure functions (no database) — these never change
# ---------------------------------------------------------------------------

def weighted_merge(
    public_scores: list[float],
    real_scores: list[float],
    public_weight: float,
    real_weight: float,
) -> list[float]:
    """Combine two score datasets using weighted sampling without replacement."""
    n_public = int(len(public_scores) * public_weight)
    n_real = int(len(real_scores) * real_weight)

    sampled_public = random.sample(public_scores, min(n_public, len(public_scores)))
    sampled_real = random.sample(real_scores, min(n_real, len(real_scores)))

    return sampled_public + sampled_real


def calculate_percentile(user_score: float, combined_dataset: list[float]) -> float:
    """Percentile of user_score within combined_dataset (0–100).

    Formula: (count of values below user_score) / total_values × 100.
    Returns 50.0 if the dataset is empty (neutral).
    """
    if not combined_dataset:
        return 50.0

    all_scores = combined_dataset + [user_score]
    all_scores.sort()

    below = sum(1 for s in all_scores if s < user_score)
    return round((below / len(all_scores)) * 100, 1)


def compute_percentile_thresholds(
    scores: list[float],
    percentiles: list[float] | None = None,
) -> dict[float, float]:
    """Score threshold for each requested percentile (e.g. P25, P75)."""
    if percentiles is None:
        percentiles = [10, 25, 50, 75, 90, 99]

    if not scores:
        return {p: 0.0 for p in percentiles}

    sorted_scores = sorted(scores)
    n = len(sorted_scores)
    thresholds: dict[float, float] = {}

    for p in percentiles:
        index = int(math.ceil(p / 100 * n)) - 1
        index = max(0, min(index, n - 1))
        thresholds[p] = round(sorted_scores[index], 1)

    return thresholds


# ---------------------------------------------------------------------------
# Database helpers (v2 schema) — shared, no duplication
# ---------------------------------------------------------------------------

async def _load_blended_scores(
    pool: asyncpg.Pool,
    column: str,
    public_weight: float,
    real_weight: float,
) -> list[float]:
    """Merge public + real scores for one dimension column, weighted.

    Shared by every public percentile function so the fetch+merge orchestration
    lives in exactly one place.
    """
    public_rows = await pool.fetch(
        f"SELECT {column} AS score FROM public_dataset WHERE {column} IS NOT NULL"
    )
    real_rows = await pool.fetch(
        f"SELECT {column} AS score FROM benchmark_result WHERE {column} IS NOT NULL"
    )
    public_scores = [float(r["score"]) for r in public_rows]
    real_scores = [float(r["score"]) for r in real_rows]
    return weighted_merge(public_scores, real_scores, public_weight, real_weight)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def calculate_percentiles_for_user(
    pool: asyncpg.Pool,
    dimension_scores: dict[str, float],
    public_weight: float,
    real_weight: float,
) -> dict[str, float]:
    """Percentile per dimension, blending public + real datasets on the fly.

    The blending weights MUST come from the current rebalancing state
    (``app.services.rebalancing.get_current_weights``) so that percentiles and
    the displayed ``pesos`` stay consistent.

    Args:
        pool: asyncpg pool.
        dimension_scores: {'visibility': 70.0, 'friction': 50.0, ...}.
        public_weight / real_weight: blending weights (must sum to 1).

    Returns:
        {'visibility': 65.0, 'friction': 40.0, ...} — percentile per dimension.
    """
    percentiles: dict[str, float] = {}

    for dimension, column in DIMENSION_SCORE_COLUMN.items():
        merged = await _load_blended_scores(pool, column, public_weight, real_weight)
        user_score = dimension_scores.get(dimension.value, 0.0)
        percentiles[dimension.value] = calculate_percentile(user_score, merged)

    return percentiles


async def get_percentile(
    pool: asyncpg.Pool,
    dimension: Dimension,
    score: float,
    public_weight: float,
    real_weight: float,
) -> float:
    """Convenience: percentile for ONE dimension (on the fly)."""
    column = DIMENSION_SCORE_COLUMN[dimension]
    merged = await _load_blended_scores(pool, column, public_weight, real_weight)
    return calculate_percentile(score, merged)


async def get_all_percentiles(
    pool: asyncpg.Pool,
    public_weight: float,
    real_weight: float,
) -> dict[str, dict[float, float]]:
    """Percentile thresholds for every dimension (for stats endpoints)."""
    result: dict[str, dict[float, float]] = {}
    for dimension, column in DIMENSION_SCORE_COLUMN.items():
        merged = await _load_blended_scores(pool, column, public_weight, real_weight)
        result[dimension.value] = compute_percentile_thresholds(merged)
    return result