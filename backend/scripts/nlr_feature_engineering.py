"""
NLR HPC Facility PUE Data -- Feature Engineering.

Computes the five data-center maturity dimension scores from the public
NLR HPC Facility PUE dataset:
  https://data.nlr.gov/system/files/300/1757105566-esif.influx.buildingData.PUE.combined.csv.zip

Expected CSV columns (case-insensitive, flexible naming):
  Timestamp, IT Power (kW) or Power IT, Cooling (kW) or Cooling, Energy, PUE.

Usage:
    python scripts/nlr_feature_engineering.py --csv path/to/dataset.csv
    python scripts/nlr_feature_engineering.py --csv path/to/dataset.csv --out scores.json
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd


def _load_and_normalize(csv_path: str) -> pd.DataFrame:
    """Load the CSV and min-max normalize every numeric column to [0, 100]."""
    df = pd.read_csv(csv_path)

    for col in df.columns:
        if col.lower() == "timestamp":
            continue
        df[col] = pd.to_numeric(
            df[col].astype(str).str.replace(",", "."),
            errors="coerce",
        )
        mn, mx = df[col].min(), df[col].max()
        if mx > mn:
            df[col] = ((df[col] - mn) / (mx - mn) * 100).round()
        else:
            df[col] = 0.0

    return df


def _resolve_column(df: pd.DataFrame, candidates: list[str]) -> "pd.Series | None":
    """Return the first column found from a list of candidate names (case-insensitive)."""
    lower_map = {c.lower(): c for c in df.columns}
    for name in candidates:
        if name.lower() in lower_map:
            return df[lower_map[name.lower()]]
    return None


def calcular_visibilidad_cross_layer(df: pd.DataFrame) -> float:
    """Score = mean across all instrumented numeric layers.

    Represents what fraction of the physical layers have live telemetry
    and how well utilized that visibility is. Higher = better.
    """
    candidates = ["Cooling", "Energy", "Power IT", "IT Power (kW)", "HVAC (kW)", "Pumps (kW)"]
    available = [
        _resolve_column(df, [name])
        for name in candidates
        if _resolve_column(df, [name]) is not None
    ]

    if not available:
        return 0.0

    combined = pd.concat(available, axis=1)
    return round(float(combined.mean().mean()), 1)


def calcular_atribucion_friccion(df: pd.DataFrame) -> float:
    """Score = 100 - mean absolute difference between IT load and cooling.

    Lower delta = less stranded capacity at the IT-cooling interface = better score.
    Score is inverted so that higher values represent better friction attribution.
    """
    it_col = _resolve_column(df, ["Power IT", "IT Power (kW)"])
    cool_col = _resolve_column(df, ["Cooling", "Cooling (kW)"])

    if it_col is None or cool_col is None:
        return 0.0

    diff = (it_col - cool_col).abs()
    return round(float(100 - diff.mean()), 1)


def calcular_latencia_coordinacion(df: pd.DataFrame) -> float:
    """Score = (coordinated changes / workload changes) x 100.

    A workload change is a >10 % shift in IT load between consecutive rows.
    A coordinated change is when cooling also shifts >10 % in the same interval.
    Higher = faster coordination between IT workload and cooling response.
    """
    it_col = _resolve_column(df, ["Power IT", "IT Power (kW)"])
    cool_col = _resolve_column(df, ["Cooling", "Cooling (kW)"])

    if it_col is None or cool_col is None:
        return 0.0

    it_vals = it_col.tolist()
    cool_vals = cool_col.tolist()
    workload_changes = 0
    coordinated = 0

    for i in range(len(df) - 1):
        if it_vals[i] == 0 or cool_vals[i] == 0:
            continue
        delta_it = abs((it_vals[i + 1] - it_vals[i]) / it_vals[i]) * 100
        delta_cool = abs((cool_vals[i + 1] - cool_vals[i]) / cool_vals[i]) * 100
        if delta_it > 10:
            workload_changes += 1
            if delta_cool > 10:
                coordinated += 1

    if workload_changes == 0:
        return 0.0

    return round((coordinated / workload_changes) * 100, 1)


def calcular_auto_cuantificacion(df: pd.DataFrame) -> float:
    """Score = 100 - mean absolute difference between IT load and cooling.

    Approximates how well the operator can quantify the gap between
    what is consumed by IT and what cooling delivers. Higher = better.
    """
    it_col = _resolve_column(df, ["Power IT", "IT Power (kW)"])
    cool_col = _resolve_column(df, ["Cooling", "Cooling (kW)"])

    if it_col is None or cool_col is None:
        return 0.0

    diffs = (it_col - cool_col).abs()
    return round(float(100 - diffs.mean()), 1)


def calcular_bloqueantes(df: pd.DataFrame) -> float:
    """Score = percentage of time intervals where the IT-cooling gap exceeds 10 points.

    Represents how often operational blockers are present in the data.
    Higher percentage = more time spent in a blocked state.
    Note: unlike other dimensions, a higher score here is worse.
    """
    it_col = _resolve_column(df, ["Power IT", "IT Power (kW)"])
    cool_col = _resolve_column(df, ["Cooling", "Cooling (kW)"])

    if it_col is None or cool_col is None:
        return 0.0

    blocked = ((it_col - cool_col).abs() > 10).sum()
    return round((blocked / len(df)) * 100, 1)


def compute_all_scores(csv_path: str) -> dict[str, float]:
    """Run all five dimension calculations and return a score dictionary."""
    df = _load_and_normalize(csv_path)
    return {
        "visibilidad_cross_layer": calcular_visibilidad_cross_layer(df),
        "atribucion_friccion":     calcular_atribucion_friccion(df),
        "latencia_coordinacion":   calcular_latencia_coordinacion(df),
        "auto_cuantificacion":     calcular_auto_cuantificacion(df),
        "bloqueantes":             calcular_bloqueantes(df),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compute NLR dimension scores from PUE dataset CSV."
    )
    parser.add_argument("--csv", required=True, help="Path to the NLR HPC PUE CSV file")
    parser.add_argument("--out", default=None, help="Optional output JSON file path")
    args = parser.parse_args()

    if not Path(args.csv).exists():
        print(f"Error: file not found: {args.csv}", file=sys.stderr)
        sys.exit(1)

    scores = compute_all_scores(args.csv)
    output = json.dumps(scores, indent=2)
    print(output)

    if args.out:
        Path(args.out).write_text(output)
        print(f"Scores written to {args.out}", file=sys.stderr)
