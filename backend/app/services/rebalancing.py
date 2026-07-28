"""Dynamic rebalancing of benchmark weights based on population drift."""

import asyncpg

from app.core.logging import get_logger
from app.models.schemas import Dimension

logger = get_logger(__name__)

DEFAULT_WEIGHTS: dict[Dimension, float] = {
    Dimension.STRATEGIC_THINKING: 0.20,
    Dimension.EXECUTION: 0.20,
    Dimension.LEADERSHIP: 0.20,
    Dimension.INNOVATION: 0.20,
    Dimension.COLLABORATION: 0.20,
}


async def get_current_weights(pool: asyncpg.Pool) -> dict[str, float]:
    rows = await pool.fetch("SELECT dimension, weight FROM benchmark_weights")
    if not rows:
        return {d.value: w for d, w in DEFAULT_WEIGHTS.items()}
    return {row["dimension"]: float(row["weight"]) for row in rows}


async def rebalance_weights(pool: asyncpg.Pool, drift_threshold: float = 0.15) -> bool:
    """
    Rebalance dimension weights when population variance drifts beyond threshold.
    Returns True if rebalancing was applied.
    """
    stats = await pool.fetch(
        """
        SELECT dimension, AVG(score) AS mean, STDDEV(score) AS std_dev
        FROM benchmark_scores
        GROUP BY dimension
        """
    )
    if len(stats) < len(Dimension):
        logger.info("rebalance_skipped", reason="insufficient_data")
        return False

    means = [float(s["mean"]) for s in stats]
    global_mean = sum(means) / len(means)
    max_drift = max(abs(m - global_mean) / global_mean for m in means if global_mean)

    if max_drift < drift_threshold:
        logger.info("rebalance_skipped", reason="within_threshold", drift=max_drift)
        return False

    # Inverse-variance weighting
    variances = []
    for s in stats:
        std = float(s["std_dev"] or 1.0)
        variances.append((s["dimension"], 1.0 / (std**2)))

    total_inv_var = sum(v for _, v in variances)
    async with pool.acquire() as conn:
        async with conn.transaction():
            for dimension, inv_var in variances:
                weight = round(inv_var / total_inv_var, 4)
                await conn.execute(
                    """
                    INSERT INTO benchmark_weights (dimension, weight, updated_at)
                    VALUES ($1, $2, NOW())
                    ON CONFLICT (dimension) DO UPDATE
                    SET weight = EXCLUDED.weight, updated_at = NOW()
                    """,
                    dimension,
                    weight,
                )

    logger.info("rebalance_applied", drift=max_drift)
    return True
