"""Tests for the report PDF HTML builder (app/api/v1/report.py)."""

from app.api.v1.report import _build_default_html
from app.core.dimensions import DIMENSION_SCORE_COLUMN


class _FakeRecord(dict):
    def get(self, key, default=None):
        return dict.get(self, key, default)


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