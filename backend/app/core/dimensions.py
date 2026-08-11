"""Single source of truth for the 5 data-center maturity dimensions.

Centraliza el mapeo entre el enum ``Dimension`` y las columnas fijas del
esquema v2 (``public_dataset`` / ``benchmark_result``), el orden canónico de
las dimensiones y la normalización de respuestas 1-5 → 0-100.

Cualquier módulo que necesite conocer las dimensiones o sus columnas debe
importar desde aquí, evitando duplicar este conocimiento.
"""

from app.models.schemas import Dimension

# Orden canónico de las dimensiones del benchmark.
ORDERED_DIMENSIONS: list[Dimension] = [
    Dimension.VISIBILITY,
    Dimension.FRICTION,
    Dimension.LATENCY,
    Dimension.QUANTIFICATION,
    Dimension.BLOCKERS,
]

# Enum → columna fija del esquema v2 (public_dataset / benchmark_result).
DIMENSION_SCORE_COLUMN: dict[Dimension, str] = {
    Dimension.VISIBILITY: "visibility_score",
    Dimension.FRICTION: "friction_score",
    Dimension.LATENCY: "latency_score",
    Dimension.QUANTIFICATION: "quantification_score",
    Dimension.BLOCKERS: "blockers_score",
}

# Mapeo inverso: columna → enum (para reconstruir resultados desde la BD).
COLUMN_TO_DIMENSION: dict[str, Dimension] = {
    column: dimension for dimension, column in DIMENSION_SCORE_COLUMN.items()
}

# Mapeo nombre corto (str) → enum, útil para parsear strings que vienen de BD.
NAME_TO_DIMENSION: dict[str, Dimension] = {d.value: d for d in ORDERED_DIMENSIONS}


def normalize_answer(value: float) -> float:
    """Normaliza una respuesta de escala 1-5 a 0-100."""
    return (value / 5) * 100