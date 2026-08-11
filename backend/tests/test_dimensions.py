"""Tests for the single source of truth of dimensions (app/core/dimensions.py)."""

from app.core.dimensions import (
    COLUMN_TO_DIMENSION,
    DIMENSION_SCORE_COLUMN,
    ORDERED_DIMENSIONS,
    normalize_answer,
)
from app.models.schemas import Dimension


def test_ordered_dimensions_contains_all_five():
    dims = set(ORDERED_DIMENSIONS)
    expected = {
        Dimension.VISIBILITY,
        Dimension.FRICTION,
        Dimension.LATENCY,
        Dimension.QUANTIFICATION,
        Dimension.BLOCKERS,
    }
    assert dims == expected


def test_every_dimension_has_a_score_column():
    assert len(DIMENSION_SCORE_COLUMN) == 5
    for dimension in ORDERED_DIMENSIONS:
        assert DIMENSION_SCORE_COLUMN[dimension].endswith("_score")


def test_column_to_dimension_is_exact_inverse():
    for dimension, column in DIMENSION_SCORE_COLUMN.items():
        assert COLUMN_TO_DIMENSION[column] == dimension
    assert len(COLUMN_TO_DIMENSION) == len(DIMENSION_SCORE_COLUMN)


def test_normalize_answer():
    assert normalize_answer(5) == 100.0
    assert normalize_answer(1) == 20.0
    assert normalize_answer(0) == 0.0
    assert normalize_answer(3) == 60.0