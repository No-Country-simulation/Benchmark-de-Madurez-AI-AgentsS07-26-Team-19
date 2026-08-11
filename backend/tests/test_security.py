"""Tests for security helpers (app/core/security.py)."""

from app.core.security import generate_anon_session_id


def test_generate_anon_session_id_fits_varchar_32():
    session_id = generate_anon_session_id()
    assert len(session_id) <= 32
    assert session_id  # no vacío