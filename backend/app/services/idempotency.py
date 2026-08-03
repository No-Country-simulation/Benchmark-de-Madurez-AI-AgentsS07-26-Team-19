"""Idempotency support for diagnostic submission.

Implements the Stripe idempotency pattern (reference:
https://docs.stripe.com/api/idempotent_requests) at the application layer.
The session_id acts as the Idempotency-Key: re-submitting the same answers
under the same session replays the stored result, while different answers
under the same session conflict (HTTP 409).

Concurrency is guarded with a PostgreSQL transaction-scoped advisory lock
(https://www.postgresql.org/docs/current/functions-admin.html), so two
simultaneous submissions for the same session serialize into a single row.
"""

import hashlib
import json
from collections.abc import Iterable
from typing import Any

from app.models.schemas import DiagnosticAnswer


class IdempotencyConflictError(Exception):
    """Raised when a session already has a diagnostic with different answers."""


def _normalize(
    answers: Iterable[DiagnosticAnswer | dict[str, Any]] | str | bytes,
) -> list[tuple[str, int]]:
    """Convert DiagnosticAnswer objects, raw dicts, or a JSON string into pairs."""
    if isinstance(answers, (str, bytes)):
        answers = json.loads(answers)
    items: list[tuple[str, int]] = []
    for answer in answers:
        if isinstance(answer, DiagnosticAnswer):
            items.append((answer.question_id, answer.value))
        elif isinstance(answer, dict):
            items.append((answer["question_id"], answer["value"]))
        else:
            raise TypeError(f"Unsupported answer type: {type(answer)}")
    return items


def compute_answers_fingerprint(
    answers: Iterable[DiagnosticAnswer | dict[str, Any]] | str | bytes,
) -> str:
    """Return a SHA-256 fingerprint of the answers, independent of ordering.

    The fingerprint is computed over the sorted (question_id, value) pairs so
    that reordering answers does not change the result.
    """
    normalized = sorted(_normalize(answers))
    payload = json.dumps(normalized, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()
