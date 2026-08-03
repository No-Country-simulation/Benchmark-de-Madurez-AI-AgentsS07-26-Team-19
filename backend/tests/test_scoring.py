from app.models.schemas import DiagnosticAnswer, Dimension
from app.services.scoring import compute_dimension_scores, compute_overall_score


def test_compute_dimension_scores():
    answers = [
        DiagnosticAnswer(question_id="vcl_01", value=5),
        DiagnosticAnswer(question_id="vcl_02", value=3),
        DiagnosticAnswer(question_id="af_01", value=4),
    ]
    question_dims = {
        "vcl_01": Dimension.VISIBILIDAD_CROSS_LAYER,
        "vcl_02": Dimension.VISIBILIDAD_CROSS_LAYER,
        "af_01": Dimension.ATRIBUCION_FRICCION,
    }

    scores = compute_dimension_scores(answers, question_dims)

    vcl = next(s for s in scores if s.dimension == Dimension.VISIBILIDAD_CROSS_LAYER)
    af = next(s for s in scores if s.dimension == Dimension.ATRIBUCION_FRICCION)

    assert vcl.score == 80.0  # avg(5,3) = 4 → 80%
    assert af.score == 80.0  # 4/5 = 80%


def test_compute_overall_score():
    from app.models.schemas import DimensionScore

    dimensions = [
        DimensionScore(dimension=Dimension.VISIBILIDAD_CROSS_LAYER, score=80.0),
        DimensionScore(dimension=Dimension.BLOQUEANTES, score=60.0),
    ]
    assert compute_overall_score(dimensions) == 70.0
