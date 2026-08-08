"""Scoring across the 5 data-center maturity dimensions."""

from collections import defaultdict

from app.models.schemas import DiagnosticAnswer, Dimension, DimensionScore


DIMENSIONS = list(Dimension)


def compute_dimension_scores(
    answers: list[DiagnosticAnswer],
    question_dimensions: dict[int, Dimension],   # ← AHORA SÍ, int
) -> list[DimensionScore]:
    """Agrupa respuestas por dimensión en escala 0-100.

    question_dimensions: mapea cada question_id (int) a su Dimension.
    """
    totals: dict[Dimension, list[int]] = defaultdict(list)

    for answer in answers:
        dimension = question_dimensions.get(answer.question_id)  # key = int
        if dimension:
            totals[dimension].append(answer.value)

    scores: list[DimensionScore] = []
    for dimension in DIMENSIONS:
        values = totals.get(dimension, [])
        if values:
            avg = sum(values) / len(values)
            score = round((avg / 5) * 100, 2)
        else:
            score = 0.0
        scores.append(DimensionScore(dimension=dimension, score=score))

    return scores


def compute_overall_score(dimensions: list[DimensionScore]) -> float:
    if not dimensions:
        return 0.0
    return round(sum(d.score for d in dimensions) / len(dimensions), 2)
