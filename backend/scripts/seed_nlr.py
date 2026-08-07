"""
Seed the NLR benchmark dataset: questions, synthetic scores, and percentile buckets.

Dimensions correspond to the five data-center maturity dimensions:
  - visibilidad_cross_layer  : unified real-time visibility across IT, cooling, and power
  - atribucion_friccion      : ability to identify which physical interface loses capacity
  - latencia_coordinacion    : speed at which cooling/power respond to workload changes
  - auto_cuantificacion      : knowledge of current stranded capacity as a percentage
  - bloqueantes              : organizational or technical blockers preventing resolution

Usage:
    python scripts/seed_nlr.py
    # or from backend/:
    python -m scripts.seed_nlr
"""

import asyncio
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncpg

from nlr_feature_engineering import (
    calcular_visibilidad_cross_layer,
    calcular_atribucion_friccion,
    calcular_latencia_coordinacion,
    calcular_auto_cuantificacion,
    calcular_bloqueantes,
)

from app.core.config import get_settings

DIMENSIONS = [
    "visibilidad_cross_layer",
    "atribucion_friccion",
    "latencia_coordinacion",
    "auto_cuantificacion",
    "bloqueantes",
]

# One question per dimension; extend as needed.
QUESTIONS = [
    # Visibilidad cross-layer
    (
        "vcl_01", "visibilidad_cross_layer",
        "Does your facility have a unified real-time view of IT load, cooling, and energy consumption?",
        1,
    ),
    (
        "vcl_02", "visibilidad_cross_layer",
        "How many physical layers (IT, cooling, power, network) are instrumented with live telemetry?",
        2,
    ),
    # Atribucion de friccion
    (
        "af_01", "atribucion_friccion",
        "Can you identify in which physical interface (IT-cooling, cooling-power, etc.) you lose the most stranded capacity?",
        3,
    ),
    (
        "af_02", "atribucion_friccion",
        "Do you have automated alerts when the delta between IT load and cooling output exceeds a threshold?",
        4,
    ),
    # Latencia de coordinacion
    (
        "lc_01", "latencia_coordinacion",
        "When workload spikes by more than 20 %, how quickly does your cooling system respond (in minutes)?",
        5,
    ),
    (
        "lc_02", "latencia_coordinacion",
        "Do your workload scheduling decisions factor in real-time cooling and power availability?",
        6,
    ),
    # Auto-cuantificacion
    (
        "aq_01", "auto_cuantificacion",
        "Do you know your current stranded capacity as a percentage of total commissioned capacity?",
        7,
    ),
    (
        "aq_02", "auto_cuantificacion",
        "Is stranded capacity tracked and reported at least weekly?",
        8,
    ),
    # Bloqueantes
    (
        "bl_01", "bloqueantes",
        "If you identified the root cause of stranded capacity today, what would prevent you from resolving it within 30 days?",
        9,
    ),
    (
        "bl_02", "bloqueantes",
        "Do organizational silos between facilities, IT, and operations teams slow down coordination decisions?",
        10,
    ),
]


async def seed_questions(conn: asyncpg.Connection) -> None:
    """Insert benchmark questions, updating on conflict."""
    for qid, dim, text, order in QUESTIONS:
        await conn.execute(
            """
            INSERT INTO benchmark_questions (id, dimension, text, display_order)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id) DO UPDATE
            SET text = EXCLUDED.text,
                dimension = EXCLUDED.dimension,
                display_order = EXCLUDED.display_order
            """,
            qid, dim, text, order,
        )
    print(f"  OK  Seeded {len(QUESTIONS)} questions")


async def seed_scores(conn: asyncpg.Connection) -> None:

    count = await conn.fetchval(
        """
        SELECT COUNT(*)
        FROM benchmark_scores
        WHERE source = 'public_dataset'
        """
    )

    if count > 0:
        print(" -- Public benchmark already exists, skipping")
        return

    scores = {
        "visibilidad_cross_layer": calcular_visibilidad_cross_layer(),
        "atribucion_friccion": calcular_atribucion_friccion(),
        "latencia_coordinacion": calcular_latencia_coordinacion(),
        "auto_cuantificacion": calcular_auto_cuantificacion(),
        "bloqueantes": calcular_bloqueantes(),
    }

    rows = [
        (dimension, score)
        for dimension, score in scores.items()
    ]

    await conn.executemany(
        """
        INSERT INTO benchmark_scores
            (dimension, score, source)
        VALUES ($1, $2, 'public_dataset')
        """,
        rows,
    )

    print("OK Benchmark público cargado")
    print(scores)

async def seed_percentiles(conn: asyncpg.Connection) -> None:
    """Precompute percentile buckets from the seeded scores."""
    count = await conn.fetchval("SELECT COUNT(*) FROM benchmark_percentiles")
    if count > 0:
        print(f"  --  benchmark_percentiles already has {count} rows, skipping")
        return

    for dim in DIMENSIONS:
        scores = await conn.fetch(
            "SELECT score FROM benchmark_scores WHERE dimension = $1 ORDER BY score",
            dim,
        )
        if not scores:
            continue

        total = len(scores)
        for bucket in range(0, 101, 5):
            below = sum(1 for s in scores if float(s["score"]) <= bucket)
            pct = round((below / total) * 100, 2)
            await conn.execute(
                """
                INSERT INTO benchmark_percentiles (dimension, score_bucket, percentile)
                VALUES ($1, $2, $3)
                ON CONFLICT (dimension, score_bucket) DO NOTHING
                """,
                dim, bucket, pct,
            )
    print("  OK  Seeded percentile buckets")


async def seed_weights(conn: asyncpg.Connection) -> None:
    """Insert default equal weights for each dimension."""
    for dim in DIMENSIONS:
        await conn.execute(
            """
            INSERT INTO benchmark_weights (dimension, weight)
            VALUES ($1, 0.2000)
            ON CONFLICT (dimension) DO NOTHING
            """,
            dim,
        )
    print("  OK  Seeded dimension weights")


async def main() -> None:
    settings = get_settings()
    print("Connecting to database...")

    print("HOST:", settings.postgres_host)
    print("PORT:", settings.postgres_port)
    print("USER:", settings.postgres_user)
    print("DB:", settings.postgres_db)
    print("URL:", settings.async_database_url)
    pool = await asyncpg.create_pool(dsn=settings.async_database_url)
    async with pool.acquire() as conn:
        print("Seeding NLR benchmark dataset...")
        await seed_questions(conn)
        await seed_scores(conn)
        await seed_percentiles(conn)
        await seed_weights(conn)

    await pool.close()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())