"""Tests para el scoring v2 (dimensiones cortas + question_id int).

NOTA: la semántica del cálculo no cambió (promedio de valores 1-5 → 0-100),
solo los nombres de dimensión y el tipo de clave del question_id.
"""

from app.models.schemas import DiagnosticAnswer, Dimension, DimensionScore
from app.services.scoring import compute_dimension_scores, compute_overall_score


def test_compute_dimension_scores():
    """Agrupa por dimensión y normaliza el promedio a escala 0-100."""
    answers = [
        DiagnosticAnswer(question_id=1, value=5),   # visibility
        DiagnosticAnswer(question_id=2, value=3),   # visibility
        DiagnosticAnswer(question_id=7, value=4),   # friction
    ]
    question_dims = {
        1: Dimension.VISIBILITY,
        2: Dimension.VISIBILITY,
        7: Dimension.FRICTION,
    }

    scores = compute_dimension_scores(answers, question_dims)

    vis = next(s for s in scores if s.dimension == Dimension.VISIBILITY)
    fri = next(s for s in scores if s.dimension == Dimension.FRICTION)

    assert vis.score == 80.0  # avg(5,3) = 4 → 80%
    assert fri.score == 80.0  # 4/5 = 80%


def test_missing_dimension_returns_zero():
    """Si ninguna respuesta cae en una dimensión, su score es 0.0."""
    answers = [
        DiagnosticAnswer(question_id=1, value=5),   # solo visibility
    ]
    question_dims = {1: Dimension.VISIBILITY}

    scores = compute_dimension_scores(answers, question_dims)

    blocker = next(s for s in scores if s.dimension == Dimension.BLOCKERS)
    assert blocker.score == 0.0


def test_compute_overall_score():
    """Overall = promedio simple de los scores de dimensión."""
    dimensions = [
        DimensionScore(dimension=Dimension.VISIBILITY, score=80.0),
        DimensionScore(dimension=Dimension.FRICTION, score=60.0),
    ]
    assert compute_overall_score(dimensions) == 70.0


def test_compute_overall_score_empty():
    """Sin dimensiones, overall = 0.0 (evita división por cero)."""
    assert compute_overall_score([]) == 0.0