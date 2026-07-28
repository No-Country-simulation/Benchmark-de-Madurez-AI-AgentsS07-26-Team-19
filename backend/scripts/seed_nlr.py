"""
Seed the NLR benchmark dataset: questions, sample scores, and percentiles.

Usage:
    python -m scripts.seed_nlr
    # or from backend/:
    python scripts/seed_nlr.py
"""

import asyncio
import random
import sys
from pathlib import Path

import asyncpg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings

DIMENSIONS = [
    "strategic_thinking",
    "execution",
    "leadership",
    "innovation",
    "collaboration",
]

QUESTIONS = [
    ("st_01", "strategic_thinking", "I regularly set long-term goals aligned with organizational vision.", 1),
    ("st_02", "strategic_thinking", "I analyze market trends before making strategic decisions.", 2),
    ("ex_01", "execution", "I consistently deliver projects on time and within scope.", 3),
    ("ex_02", "execution", "I break complex tasks into actionable steps.", 4),
    ("ld_01", "leadership", "I inspire others to perform at their best.", 5),
    ("ld_02", "leadership", "I provide clear direction during uncertainty.", 6),
    ("in_01", "innovation", "I encourage creative solutions to problems.", 7),
    ("in_02", "innovation", "I am comfortable challenging the status quo.", 8),
    ("co_01", "collaboration", "I actively seek diverse perspectives before deciding.", 9),
    ("co_02", "collaboration", "I build trust across teams and departments.", 10),
]


async def seed_questions(conn: asyncpg.Connection) -> None:
    for qid, dim, text, order in QUESTIONS:
        await conn.execute(
            """
            INSERT INTO benchmark_questions (id, dimension, text, display_order)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id) DO UPDATE
            SET text = EXCLUDED.text, dimension = EXCLUDED.dimension, display_order = EXCLUDED.display_order
            """,
            qid, dim, text, order,
        )
    print(f"  ✓ Seeded {len(QUESTIONS)} questions")


async def seed_scores(conn: asyncpg.Connection, samples_per_dim: int = 200) -> None:
    count = await conn.fetchval("SELECT COUNT(*) FROM benchmark_scores")
    if count > 0:
        print(f"  ↷ benchmark_scores already has {count} rows, skipping")
        return

    rows = []
    for dim in DIMENSIONS:
        mean = random.uniform(55, 75)
        std = random.uniform(8, 15)
        for _ in range(samples_per_dim):
            score = max(0, min(100, random.gauss(mean, std)))
            rows.append((dim, round(score, 2)))

    await conn.executemany(
        "INSERT INTO benchmark_scores (dimension, score) VALUES ($1, $2)",
        rows,
    )
    print(f"  ✓ Seeded {len(rows)} benchmark scores")


async def seed_percentiles(conn: asyncpg.Connection) -> None:
    count = await conn.fetchval("SELECT COUNT(*) FROM benchmark_percentiles")
    if count > 0:
        print(f"  ↷ benchmark_percentiles already has {count} rows, skipping")
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
    print("  ✓ Seeded percentile buckets")


async def main() -> None:
    settings = get_settings()
    print(f"Connecting to {settings.database_url} ...")

    pool = await asyncpg.create_pool(dsn=settings.async_database_url)
    async with pool.acquire() as conn:
        print("Seeding NLR dataset...")
        await seed_questions(conn)
        await seed_scores(conn)
        await seed_percentiles(conn)

    await pool.close()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
