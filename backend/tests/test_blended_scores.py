"""Tests for the shared blended-scores DB orchestration (percentiles)."""

from app.models.schemas import Dimension
from app.services.percentiles import get_percentile


class _FakePool:
    def __init__(self, public: list[float], real: list[float]) -> None:
        self.public = public
        self.real = real

    async def fetch(self, query: str, *args: object) -> list[dict]:
        if "FROM public_dataset" in query:
            return [{"score": s} for s in self.public]
        if "FROM benchmark_result" in query:
            return [{"score": s} for s in self.real]
        return []


async def test_get_percentile_merges_public_and_real():
    pool = _FakePool(public=[10, 20, 30, 40], real=[50, 60])

    # 100% public: user=20 vs [10,20,30,40] → 1 of 4 are below → 25%
    only_public = await get_percentile(pool, Dimension.VISIBILITY, 20, 1.0, 0.0)
    assert only_public == 25.0

    # 100% real: user=55 vs [50,60] → 1 of 2 below → 50%
    only_real = await get_percentile(pool, Dimension.VISIBILITY, 55, 0.0, 1.0)
    assert only_real == 50.0


async def test_get_percentile_empty_dataset_returns_neutral():
    pool = _FakePool(public=[], real=[])
    assert await get_percentile(pool, Dimension.VISIBILITY, 50, 1.0, 0.0) == 50.0