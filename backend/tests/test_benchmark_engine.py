"""Tests for the benchmark_engine service, including idempotent persistence."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest

from app.models.schemas import DiagnosticAnswer
from app.services.benchmark_engine import DiagnosticOutcome, save_diagnostic_idempotent
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
        if "FROM diagnostics" in args[0]:
            return self.pool.stored_row
        if "INSERT INTO diagnostics" in args[0]:
            return {"id": self.pool.next_id}
        return None


class _FakePoolCtx:
    def __init__(self, pool: "_FakePool") -> None:
        self.pool = pool

    async def __aenter__(self) -> _FakeConn:
        return _FakeConn(self.pool)

    async def __aexit__(self, *args: object) -> bool:
        return False


class _FakePool:
    def __init__(self, stored_row: dict[str, Any] | None = None) -> None:
        self.stored_row = stored_row
        self.next_id = uuid4()

    def acquire(self) -> _FakePoolCtx:
        return _FakePoolCtx(self)


async def test_save_diagnostic_idempotent_creates_new() -> None:
    pool = _FakePool()
    fingerprint = compute_answers_fingerprint(
        [DiagnosticAnswer(question_id="vcl_01", value=5)]
    )

    outcome = await save_diagnostic_idempotent(
        pool,
        session_id="sess-1",
        fingerprint=fingerprint,
        overall_score=80.0,
        dimension_scores={"visibilidad_cross_layer": {"score": 80.0}},
        answers=[{"question_id": "vcl_01", "value": 5}],
    )

    assert isinstance(outcome, DiagnosticOutcome)
    assert outcome.replayed is False
    assert outcome.diagnostic_id == pool.next_id
    assert outcome.created_at <= datetime.now(UTC)


async def test_save_diagnostic_idempotent_replays_existing() -> None:
    stored_id = uuid4()
    stored_at = datetime.now(UTC)
    pool = _FakePool(
        stored_row={
            "id": stored_id,
            "session_id": "sess-1",
            "answers": '[{"question_id": "vcl_01", "value": 5}]',
            "created_at": stored_at,
        }
    )
    fingerprint = compute_answers_fingerprint(
        [DiagnosticAnswer(question_id="vcl_01", value=5)]
    )

    outcome = await save_diagnostic_idempotent(
        pool,
        session_id="sess-1",
        fingerprint=fingerprint,
        overall_score=80.0,
        dimension_scores={"visibilidad_cross_layer": {"score": 80.0}},
        answers=[{"question_id": "vcl_01", "value": 5}],
    )

    assert outcome.replayed is True
    assert outcome.diagnostic_id == stored_id
    assert outcome.created_at == stored_at


async def test_save_diagnostic_idempotent_conflicts_on_different_answers() -> None:
    stored_id = uuid4()
    stored_at = datetime.now(UTC)
    pool = _FakePool(
        stored_row={
            "id": stored_id,
            "session_id": "sess-1",
            "answers": '[{"question_id": "vcl_01", "value": 3}]',
            "created_at": stored_at,
        }
    )
    fingerprint = compute_answers_fingerprint(
        [DiagnosticAnswer(question_id="vcl_01", value=5)]
    )

    with pytest.raises(IdempotencyConflictError):
        await save_diagnostic_idempotent(
            pool,
            session_id="sess-1",
            fingerprint=fingerprint,
            overall_score=80.0,
            dimension_scores={"visibilidad_cross_layer": {"score": 80.0}},
            answers=[{"question_id": "vcl_01", "value": 5}],
        )
