from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class Dimension(str, Enum):
    STRATEGIC_THINKING = "strategic_thinking"
    EXECUTION = "execution"
    LEADERSHIP = "leadership"
    INNOVATION = "innovation"
    COLLABORATION = "collaboration"


class DiagnosticAnswer(BaseModel):
    question_id: str
    value: int = Field(ge=1, le=5)


class DiagnosticSubmitRequest(BaseModel):
    session_id: str | None = None
    answers: list[DiagnosticAnswer] = Field(min_length=1)


class DimensionScore(BaseModel):
    dimension: Dimension
    score: float = Field(ge=0, le=100)
    percentile: float | None = None


class DiagnosticResult(BaseModel):
    id: UUID
    session_id: str
    overall_score: float
    dimensions: list[DimensionScore]
    created_at: datetime


class DiagnosticResponse(BaseModel):
    diagnostic: DiagnosticResult
    message: str = "Diagnostic submitted successfully"


class BenchmarkQuestion(BaseModel):
    id: str
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
    diagnostic_id: UUID
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
