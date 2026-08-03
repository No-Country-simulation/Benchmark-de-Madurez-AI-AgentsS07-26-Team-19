"""Dynamic rebalancing of public vs real dataset weights.

Implements the progressive blending formula defined in issue #23:

    if real_count < 20:
        real_weight = real_count / 100
    else:
        real_weight = 0.2 + (real_count - 20) * 0.004

    public_weight = 1 - real_weight

The real_weight is capped at MAX_REAL_WEIGHT (0.80) so that the public
seed dataset always contributes at least 20 % of the benchmark population,
preserving statistical stability when real submissions are few or biased.

Design pattern: Strategy
    compute_weights() is a pure function that encapsulates the blending
    algorithm. It can be swapped or extended without touching the callers.

References:
    - Issue #23: https://github.com/No-Country-simulation/Benchmark-de-Madurez-AI-AgentsS07-26-Team-19/issues/23
    - FastAPI BackgroundTasks: https://fastapi.tiangolo.com/tutorial/background-tasks/
    - asyncpg transactions: https://magicstack.github.io/asyncpg/current/api/index.html#asyncpg.connection.Connection.transaction
"""

import asyncpg

from app.core.logging import get_logger
from app.models.schemas import Dimension

logger = get_logger(__name__)

MAX_REAL_WEIGHT: float = 0.80  # public dataset always contributes >= 20 %


def compute_weights(real_count: int) -> tuple[float, float]:
    """Return (public_weight, real_weight) for a given number of real responses.

    Implements the progressive blending formula from issue #23.
    The real weight grows linearly as more real diagnostics accumulate,
    but never exceeds MAX_REAL_WEIGHT.

    Args:
        real_count: Total number of real diagnostic submissions stored.

    Returns:
        Tuple of (public_weight, real_weight), both in [0, 1] summing to 1.

    Raises:
        ValueError: If real_count is negative.
    """
    if real_count < 0:
        raise ValueError(f"real_count must be >= 0, got {real_count}")

    if real_count < 20:
        real_weight = real_count / 100
    else:
        real_weight = 0.2 + (real_count - 20) * 0.004

    real_weight = min(real_weight, MAX_REAL_WEIGHT)
    real_weight = round(real_weight, 4)
    public_weight = round(1.0 - real_weight, 4)

    return public_weight, real_weight


async def run_rebalancing(pool: asyncpg.Pool) -> tuple[float, float]:
    """Count real diagnostics, compute new weights, and persist them.

    Designed to run as a FastAPI BackgroundTask after each new diagnostic
    submission. All DB writes are wrapped in a single transaction so that
    a failure leaves no partial state.

    Returns:
        Tuple of (public_weight, real_weight) that were stored.
    """
    async with pool.acquire() as conn:
        real_count: int = await conn.fetchval("SELECT COUNT(*) FROM diagnostics")
        public_weight, real_weight = compute_weights(real_count)

        dim_weight = round(public_weight / len(Dimension), 4)

        async with conn.transaction():
            for dim in Dimension:
                await conn.execute(
                    """
                    INSERT INTO benchmark_weights (dimension, weight, updated_at)
                    VALUES ($1, $2, NOW())
                    ON CONFLICT (dimension) DO UPDATE
                    SET weight = EXCLUDED.weight, updated_at = NOW()
                    """,
                    dim.value,
                    dim_weight,
                )

            await conn.execute(
                """
                INSERT INTO rebalancing_config (real_count, real_weight, pub_weight, updated_at)
                VALUES ($1, $2, $3, NOW())
                """,
                real_count,
                real_weight,
                public_weight,
            )

    logger.info(
        "rebalancing_applied",
        real_count=real_count,
        real_weight=real_weight,
        public_weight=public_weight,
    )
    return public_weight, real_weight


async def get_current_weights(pool: asyncpg.Pool) -> dict:
    """Return the latest rebalancing state from the database.

    Falls back to the initial state (all public, 0 real) if no record exists.
    """
    row = await pool.fetchrow(
        """
        SELECT real_count, real_weight, pub_weight, updated_at
        FROM rebalancing_config
        ORDER BY id DESC
        LIMIT 1
        """
    )
    if row:
        return {
            "real_count": row["real_count"],
            "real_weight": float(row["real_weight"]),
            "public_weight": float(row["pub_weight"]),
            "updated_at": row["updated_at"],
        }
    return {"real_count": 0, "real_weight": 0.0, "public_weight": 1.0, "updated_at": None}
