"""Tests for the idempotency fingerprint (issue #26, v2 key types)."""

from app.models.schemas import DiagnosticAnswer
from app.services.idempotency import compute_answers_fingerprint


def test_fingerprint_order_independent() -> None:
    a = [
        DiagnosticAnswer(question_id=1, value=5),
        DiagnosticAnswer(question_id=2, value=3),
    ]
    b = [
        DiagnosticAnswer(question_id=2, value=3),
        DiagnosticAnswer(question_id=1, value=5),
    ]
    assert compute_answers_fingerprint(a) == compute_answers_fingerprint(b)


def test_fingerprint_detects_different_answers() -> None:
    a = [
        DiagnosticAnswer(question_id=1, value=5),
        DiagnosticAnswer(question_id=2, value=3),
    ]
    b = [
        DiagnosticAnswer(question_id=1, value=5),
        DiagnosticAnswer(question_id=2, value=4),
    ]
    assert compute_answers_fingerprint(a) != compute_answers_fingerprint(b)


def test_fingerprint_handles_json_string() -> None:
    a = '[{"question_id": 1, "value": 5}, {"question_id": 2, "value": 3}]'
    b = [
        DiagnosticAnswer(question_id=1, value=5),
        DiagnosticAnswer(question_id=2, value=3),
    ]
    assert compute_answers_fingerprint(a) == compute_answers_fingerprint(b)