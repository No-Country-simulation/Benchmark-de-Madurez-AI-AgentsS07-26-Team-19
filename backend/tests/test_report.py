"""Tests for the report PDF HTML builder (app/api/v1/report.py)."""

import app.core.database as database
from app.api.v1.report import _build_default_html
from app.core.config import Settings
from app.core.dimensions import DIMENSION_SCORE_COLUMN


class _FakeRecord(dict):
    def get(self, key, default=None):
        return dict.get(self, key, default)


def test_generate_pdf_returns_501_when_service_not_configured(monkeypatch):
    from fastapi.testclient import TestClient

    from app.core.config import get_settings
    from app.main import create_app

    monkeypatch.setattr(database, "_pool", object())

    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        pdf_service_url="", _env_file=None
    )
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post("/api/v1/report/pdf", json={"diagnostic_id": 1})

    assert response.status_code == 501
    assert "client-side" in response.json()["detail"]


def test_build_default_html_includes_all_dimensions():
    record = _FakeRecord(
        {
            "overall_score": 80.0,
            "visibility_score": 80.0,
            "friction_score": 70.0,
            "latency_score": 60.0,
            "quantification_score": 50.0,
            "blockers_score": 40.0,
        }
    )
    html = _build_default_html(record)

    assert "NLR Data Center Maturity Report" in html
    assert "<strong>Overall Score:</strong> 80.0" in html
    for dimension in DIMENSION_SCORE_COLUMN:
        assert dimension.value.title() in html


def test_build_default_html_renders_na_when_missing_score():
    record = _FakeRecord({"overall_score": 80.0})
    html = _build_default_html(record)

    assert "N/A" in html
    for dimension in DIMENSION_SCORE_COLUMN:
        assert dimension.value.title() in html