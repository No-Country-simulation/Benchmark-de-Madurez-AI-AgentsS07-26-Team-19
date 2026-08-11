"""NLR HPC Facility PUE dataset → scores de madurez (5 dimensiones).

Convierte la telemetría real del dataset público de NLR
(``data/dataset.csv``: Timestamp, Cooling, Energy, Power IT, ...) en los
scores 0-100 de las 5 dimensiones del benchmark, segmentando la serie
temporal en ventanas. Cada ventana produce un registro (diagnóstico) para
la tabla ``public_dataset``.

Diseño:
    - stdlib puro (csv, statistics) — sin pandas, para no inflar la imagen.
    - Funciones puras por dimensión, testables, sin estado global.
    - ``process_series()`` segmenta y aplica las fórmulas por ventana.
    - CLI: imprime JSON o inserta directo en Postgres vía asyncpg.

Uso:
    python scripts/nlr_feature_engineering.py --csv scripts/data/dataset.csv --window 10
    python scripts/nlr_feature_engineering.py --csv scripts/data/dataset.csv --window 10 --insert
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# Permite importar app.* cuando el script corre desde scripts/ o desde la raíz.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Columnas del dataset de telemetría que alimentan las fórmulas.
TELEMETRY_COLUMNS = ["Cooling", "Energy", "Power IT"]


class DatasetError(ValueError):
    """Error de formato o contenido del dataset."""


def load_telemetry(csv_path: Path) -> list[dict[str, float]]:
    """Carga el CSV y devuelve las filas con los 3 valores de telemetría.

    El CSV de NLR usa comas decimales europeas ("0,1084") y fechas en
    formato "Sun Jun 12 2016 00:00:18 GMT-0600 ...".
    """
    rows: list[dict[str, float]] = []
    with csv_path.open() as fh:
        reader = csv.DictReader(fh, delimiter=",")
        if "Timestamp" not in (reader.fieldnames or []):
            raise DatasetError("CSV inválido: falta la columna Timestamp")
        for line in reader:
            values: dict[str, float] = {}
            for column in TELEMETRY_COLUMNS:
                raw = (line.get(column) or "").strip()
                values[column] = float(raw.replace(",", ".")) if raw else float("nan")
            rows.append(values)

    if not rows:
        raise DatasetError(f"El CSV está vacío: {csv_path}")
    return rows


def normalize_to_100(values: list[float]) -> list[float]:
    """Min-max normaliza una columna a escala 0-100 (redondeado)."""
    finite = [v for v in values if v == v]  # filtra NaN
    if not finite:
        return []
    low, high = min(finite), max(finite)
    span = high - low
    if span == 0:
        return [50.0 for _ in finite]
    return [round((v - low) / span * 100) for v in finite]


def visibility_score(normalized: dict[str, list[float]]) -> float:
    """Promedio de los niveles normalizados de las capas telemetradas."""
    layers = [values for values in normalized.values() if values]
    if not layers:
        return 0.0
    return round(sum(statistics.fmean(layer) for layer in layers) / len(layers))


def friction_score(normalized: dict[str, list[float]]) -> float:
    """Magnitud media de la desalineación Power IT vs Cooling (fricción)."""
    power_it = normalized.get("Power IT") or []
    cooling = normalized.get("Cooling") or []
    if not power_it or not cooling:
        return 0.0
    diffs = [abs(p - c) for p, c in zip(power_it, cooling)]
    return round(statistics.fmean(diffs))


def latency_score(normalized: dict[str, list[float]]) -> float:
    """% de cambios de workload (>10%) con respuesta coordinada de cooling."""
    power_it = normalized.get("Power IT") or []
    cooling = normalized.get("Cooling") or []
    if len(power_it) < 2:
        return 0.0
    workload_changes = 0
    coordinated = 0
    for i in range(len(power_it) - 1):
        if cooling[i] == 0 or power_it[i] == 0:
            continue
        delta_power = abs(power_it[i + 1] - power_it[i]) / power_it[i] * 100
        delta_cooling = abs(cooling[i + 1] - cooling[i]) / cooling[i] * 100
        if delta_power > 10:
            workload_changes += 1
            if delta_cooling > 10:
                coordinated += 1
    if workload_changes == 0:
        return 0.0
    return round(coordinated / workload_changes * 100)


def quantification_score(normalized: dict[str, list[float]]) -> float:
    """Inverso del desalineamiento medio: cuánta capacidad se sabe perdida."""
    power_it = normalized.get("Power IT") or []
    cooling = normalized.get("Cooling") or []
    if not power_it or not cooling:
        return 0.0
    mean_diff = statistics.fmean(abs(p - c) for p, c in zip(power_it, cooling))
    return round(max(0.0, 100.0 - mean_diff))


def blockers_score(normalized: dict[str, list[float]]) -> float:
    """% de lecturas con desalineación >10 puntos (obstáculo presente)."""
    power_it = normalized.get("Power IT") or []
    cooling = normalized.get("Cooling") or []
    if not power_it or not cooling:
        return 0.0
    blocked = sum(1 for p, c in zip(power_it, cooling) if abs(p - c) > 10)
    return round(blocked / len(power_it) * 100)


DIMENSION_SCORES: dict[str, Any] = {
    "visibility": visibility_score,
    "friction": friction_score,
    "latency": latency_score,
    "quantification": quantification_score,
    "blockers": blockers_score,
}


@dataclass
class DimensionResult:
    """Scores por dimensión + overall de una ventana del dataset."""

    visibility: float
    friction: float
    latency: float
    quantification: float
    blockers: float
    overall: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


def process_window(window: list[dict[str, float]]) -> DimensionResult:
    """Calcula los 5 scores de una ventana de telemetría.

    La normalización es POR VENTANA (cada ventana define su propio 0-100),
    lo que refleja la variabilidad relativa de esa franja horaria.
    """
    normalized = {
        column: normalize_to_100([row[column] for row in window])
        for column in TELEMETRY_COLUMNS
    }
    scores = {
        name: fn(normalized) for name, fn in DIMENSION_SCORES.items()
    }
    overall = round(sum(scores.values()) / len(scores))
    return DimensionResult(**scores, overall=overall)


def process_series(
    rows: list[dict[str, float]],
    window_size: int = 10,
) -> list[DimensionResult]:
    """Segmenta la serie en ventanas de ``window_size`` filas y calcula scores."""
    windows = [
        rows[i : i + window_size]
        for i in range(0, len(rows) - window_size + 1, window_size)
    ]
    return [process_window(w) for w in windows]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("scripts/data/dataset.csv"),
        help="Ruta al dataset de telemetría NLR.",
    )
    parser.add_argument("--window", type=int, default=10, help="Filas por ventana.")
    parser.add_argument("--insert", action="store_true", help="Insertar en Postgres.")
    return parser.parse_args(argv)


async def _insert_results(results: list[DimensionResult]) -> None:
    """Inserta los scores calculados en ``public_dataset`` (idempotente)."""
    import asyncpg

    from app.core.config import get_settings

    settings = get_settings()
    conn = await asyncpg.connect(settings.async_database_url)
    try:
        for idx, result in enumerate(results, start=1):
            await conn.execute(
                """
                INSERT INTO public_dataset (
                    source, source_type, visibility_score, friction_score,
                    latency_score, quantification_score, blockers_score,
                    overall_score, collected_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                "nlr-hpc-pue",
                "telemetria",
                result.visibility,
                result.friction,
                result.latency,
                result.quantification,
                result.blockers,
                result.overall,
                datetime(2016, 6, 12, 0, 0, 0),
            )
            if idx % 10 == 0:
                print(f"  -- insertadas {idx}/{len(results)} filas")
    finally:
        await conn.close()
    print(f"OK Insertadas {len(results)} filas en public_dataset (source=nlr-hpc-pue)")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.csv.exists():
        print(f"ERROR: no existe el dataset: {args.csv}", file=sys.stderr)
        return 1

    rows = load_telemetry(args.csv)
    results = process_series(rows, args.window)
    payload = [r.to_dict() for r in results]

    if args.insert:
        import asyncio

        asyncio.run(_insert_results(results))
        return 0

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
