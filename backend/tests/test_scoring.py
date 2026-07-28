from app.models.schemas import DiagnosticAnswer, Dimension
from app.services.scoring import compute_dimension_scores, compute_overall_score


def test_compute_dimension_scores():
    answers = [
        DiagnosticAnswer(question_id="st_01", value=5),
        DiagnosticAnswer(question_id="st_02", value=3),
        DiagnosticAnswer(question_id="ex_01", value=4),
    ]
    question_dims = {
        "st_01": Dimension.STRATEGIC_THINKING,
        "st_02": Dimension.STRATEGIC_THINKING,
        "ex_01": Dimension.EXECUTION,
    }

    scores = compute_dimension_scores(answers, question_dims)

    st = next(s for s in scores if s.dimension == Dimension.STRATEGIC_THINKING)
    ex = next(s for s in scores if s.dimension == Dimension.EXECUTION)

    assert st.score == 80.0  # avg(5,3) = 4 → 80%
    assert ex.score == 80.0  # 4/5 = 80%


def test_compute_overall_score():
    from app.models.schemas import DimensionScore

    dimensions = [
        DimensionScore(dimension=Dimension.EXECUTION, score=80.0),
        DimensionScore(dimension=Dimension.LEADERSHIP, score=60.0),
    ]
    assert compute_overall_score(dimensions) == 70.0
