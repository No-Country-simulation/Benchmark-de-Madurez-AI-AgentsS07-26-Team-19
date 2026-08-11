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

Design (v2):
    - The blend state lives in the single-row table `rebalance_config`
      (columns public_weight / primary_weight). Every rebalance run updates
      that row; no audit history is kept (see perspective: option A).
    - Real submissions are counted from `benchmark_response`.

References:
    - Issue #23: https://github.com/No-Country-simulation/Benchmark-de-Madurez-AI-AgentsS07-26-Team-19/issues/23
    - FastAPI BackgroundTasks: https://fastapi.tiangolo.com/tutorial/background-tasks/
    - asyncpg transactions: https://magicstack.github.io/asyncpg/current/api/index.html#asyncpg.connection.Connection.transaction
"""

from dataclasses import dataclass
from datetime import datetime

import asyncpg

from app.core.logging import get_logger

logger = get_logger(__name__)

MAX_REAL_WEIGHT: float = 0.80  # public dataset always contributes >= 20 %

CONFIG_ID: int = 1  # rebalance_config is a single-row table (id = 1)


@dataclass(frozen=True)
class WeightsState:
    """Snapshot of the current public/real blending weights.

    Returned by ``get_current_weights`` so API routers can map it to the
    ``WeightsResponse`` schema without repeating the field mapping.
    """

    public_weight: float
    real_weight: float
    real_count: int
    updated_at: datetime | None


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

    v2: updates the single row of `rebalance_config` (id = CONFIG_ID).
    `real_weight` is stored in the `primary_weight` column; the sum check
    constraint (public_weight + primary_weight = 1) is applied by Postgres.

    Returns:
        Tuple of (public_weight, real_weight) that were stored.
    """
    async with pool.acquire() as conn:
        real_count: int = await conn.fetchval(
            "SELECT COUNT(*) FROM benchmark_response"
        )
        public_weight, real_weight = compute_weights(real_count)

        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO rebalance_config (id, public_weight, primary_weight,
                                              min_responses, description, updated_at)
                VALUES ($1, $2, $3, 0, 'current blend state', NOW())
                ON CONFLICT (id) DO UPDATE
                SET public_weight = EXCLUDED.public_weight,
                    primary_weight = EXCLUDED.primary_weight,
                    updated_at = NOW()
                """,
                CONFIG_ID,
                public_weight,
                real_weight,
            )

    logger.info(
        "rebalancing_applied",
        real_count=real_count,
        real_weight=real_weight,
        public_weight=public_weight,
    )
    return public_weight, real_weight


async def get_current_weights(pool: asyncpg.Pool) -> WeightsState:
    """Return the latest rebalancing state.

    Falls back to the initial state (all public, 0 real) if no record exists.
    """
    real_count: int = await pool.fetchval(
        "SELECT COUNT(*) FROM benchmark_response"
    )

    row = await pool.fetchrow(
        """
        SELECT public_weight, primary_weight, updated_at
        FROM rebalance_config
        WHERE id = $1
        """,
        CONFIG_ID,
    )

    if row:
        return WeightsState(
            real_count=real_count,
            real_weight=float(row["primary_weight"]),
            public_weight=float(row["public_weight"]),
            updated_at=row["updated_at"],
        )
    return WeightsState(
        real_count=real_count,
        real_weight=0.0,
        public_weight=1.0,
        updated_at=None,
    )