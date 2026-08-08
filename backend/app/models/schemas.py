from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Dimension(StrEnum):
    VISIBILITY       = "visibility"
    FRICTION         = "friction"
    LATENCY          = "latency"
    QUANTIFICATION   = "quantification"
    BLOCKERS         = "blockers"

class DiagnosticAnswer(BaseModel):
    question_id: int                      # ← cambia de str a int
    value: int = Field(ge=1, le=5)


class DiagnosticSubmitRequest(BaseModel):
    session_id: str | None = None
    answers: list[DiagnosticAnswer] = Field(min_length=1)


class DimensionScore(BaseModel):
    dimension: Dimension
    score: float = Field(ge=0, le=100)
    percentile: float | None = None


class DiagnosticResult(BaseModel):
    id: int                          # v2: id del benchmark_response (SERIAL)
    session_id: str
    overall_score: float
    dimensions: list[DimensionScore]
    created_at: datetime


class DiagnosticResponse(BaseModel):
    diagnostic: DiagnosticResult
    message: str = "Diagnostic submitted successfully"


class BenchmarkQuestion(BaseModel):
    id: int                                
    dimension: Dimension
    text: str
    order: int


class BenchmarkStats(BaseModel):
    dimension: Dimension
    mean: float
    std_dev: float
    sample_size: int


class PercentileLookupRequest(BaseModel):
    dimension: Dimension
    score: float = Field(ge=0, le=100)


class PercentileLookupResponse(BaseModel):
    dimension: Dimension
    score: float
    percentile: float


class ReportPdfRequest(BaseModel):
    diagnostic_id: int                # v2: id del benchmark_response (SERIAL)
    html_content: str | None = None
    template: str = "default"


class ReportPdfResponse(BaseModel):
    pdf_url: str | None = None
    pdf_base64: str | None = None
    filename: str


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None
    extra: dict[str, Any] | None = None


# --- V2 schemas for enriched diagnostic response (issue #26) ---

class WeightsResponse(BaseModel):
    """Current blending weights between public seed data and real submissions."""

    public_weight: float = Field(ge=0, le=1)
    real_weight: float = Field(ge=0, le=1)
    real_count: int = Field(ge=0)
    updated_at: datetime | None = None


class DiagnosticFrictionProfile(BaseModel):
    """Qualitative profile identifying the dominant friction dimension."""

    dominant_dimension: str
    score: float
    interpretation: str


class DiagnosticResponseV2(BaseModel):
    """Enriched diagnostic response including friction profile, quartile flag and weights."""

    diagnostic: DiagnosticResult
    perfil_friccion: DiagnosticFrictionProfile
    cuartil_superior: bool
    pesos: WeightsResponse
    message: str = "Diagnostic submitted successfully"
