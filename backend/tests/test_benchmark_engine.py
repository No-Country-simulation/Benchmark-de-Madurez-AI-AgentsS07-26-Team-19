"""Tests for the benchmark_engine service, including idempotent persistence (v2)."""

from datetime import UTC, datetime
from typing import Any

import pytest

from app.models.schemas import DiagnosticAnswer, Dimension, DimensionScore
from app.services.benchmark_engine import save_diagnostic_idempotent
from app.services.idempotency import IdempotencyConflictError, compute_answers_fingerprint


class _FakeTx:
    def __init__(self, conn: "_FakeConn") -> None:
        self.conn = conn

    async def __aenter__(self) -> "_FakeConn":
        return self.conn

    async def __aexit__(self, *args: object) -> bool:
        return False


class _FakeConn:
    def __init__(self, pool: "_FakePool") -> None:
        self.pool = pool

    def transaction(self) -> _FakeTx:
        return _FakeTx(self)

    async def execute(self, *args: str, **kwargs: object) -> str:
        return "ok"

    async def fetchrow(self, *args: str, **kwargs: object) -> dict[str, Any] | None:
        if "FROM benchmark_response" in args[0]:
            return self.pool.stored_row
        return None

    async def fetch(self, *args: str, **kwargs: object) -> list[dict[str, Any]]:
        if "FROM response_answer" in args[0]:
            return self.pool.stored_answers
        return []

    async def fetchval(self, *args: str, **kwargs: object) -> int | None:
        if "INSERT INTO benchmark_response" in args[0]:
            return self.pool.next_id
        return None


class _FakePoolCtx:
    def __init__(self, pool: "_FakePool") -> None:
        self.pool = pool

    async def __aenter__(self) -> _FakeConn:
        return _FakeConn(self.pool)

    async def __aexit__(self, *args: object) -> bool:
        return False


class _FakePool:
    def __init__(
        self,
        stored_row: dict[str, Any] | None = None,
        stored_answers: list[dict[str, Any]] | None = None,
    ) -> None:
        self.stored_row = stored_row
        self.stored_answers = stored_answers or []
        self.next_id = 999

    def acquire(self) -> _FakePoolCtx:
        return _FakePoolCtx(self)


ANSWERS = [DiagnosticAnswer(question_id=1, value=5)]
DIMS = [DimensionScore(dimension=Dimension.VISIBILITY, score=80.0)]


@pytest.mark.asyncio
async def test_save_diagnostic_idempotent_creates_new() -> None:
    pool = _FakePool()
    outcome = await save_diagnostic_idempotent(
        pool,
        session_id="sess-1",
        fingerprint=compute_answers_fingerprint(ANSWERS),
        answers=ANSWERS,
        dimension_scores=DIMS,
        overall_score=80.0,
        overall_percentile=70.0,
    )

    assert outcome.replayed is False
    assert outcome.diagnostic_id == pool.next_id
    assert outcome.created_at is not None


@pytest.mark.asyncio
async def test_save_diagnostic_idempotent_replays_existing() -> None:
    pool = _FakePool(
        stored_row={
            "id": 42,
            "created_at": datetime.now(UTC),
        },
        stored_answers=[{"question_id": 1, "answer": "5"}],
    )
    outcome = await save_diagnostic_idempotent(
        pool,
        session_id="sess-1",
        fingerprint=compute_answers_fingerprint(ANSWERS),
        answers=ANSWERS,
        dimension_scores=DIMS,
        overall_score=80.0,
        overall_percentile=70.0,
    )

    assert outcome.replayed is True
    assert outcome.diagnostic_id == 42


@pytest.mark.asyncio
async def test_save_diagnostic_idempotent_conflicts_on_different_answers() -> None:
    pool = _FakePool(
        stored_row={
            "id": 42,
            "created_at": datetime.now(UTC),
        },
        stored_answers=[{"question_id": 2, "answer": "3"}],
    )
    with pytest.raises(IdempotencyConflictError):
        await save_diagnostic_idempotent(
            pool,
            session_id="sess-1",
            fingerprint=compute_answers_fingerprint(ANSWERS),
            answers=ANSWERS,
            dimension_scores=DIMS,
            overall_score=80.0,
            overall_percentile=70.0,
        )