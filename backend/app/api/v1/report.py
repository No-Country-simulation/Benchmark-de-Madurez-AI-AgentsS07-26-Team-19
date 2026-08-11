import base64

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.config import Settings, get_settings
from app.core.dimensions import DIMENSION_SCORE_COLUMN
from app.core.logging import get_logger
from app.core.security import RATE_LIMIT, limiter
from app.deps import DbPool, PdfClientDep
from app.models.schemas import ReportPdfRequest, ReportPdfResponse
from app.services import benchmark_engine

logger = get_logger(__name__)

router = APIRouter(prefix="/report", tags=["report"])


def _fmt(value: object | None) -> str:
    """Renderiza valores numéricos del registro sin exponer None."""
    return "N/A" if value is None else str(value)


def _build_default_html(diagnostic: asyncpg.Record) -> str:
    """Genera el HTML del reporte a partir del registro v2.

    Los scores viven en columnas fijas definidas en ``app/core/dimensions.py``
    (DIMENSION_SCORE_COLUMN), así que este mapa ya no se duplica.
    """
    rows = ""
    for dimension, column in DIMENSION_SCORE_COLUMN.items():
        value = diagnostic.get(column)
        score_cell = f"<td>{_fmt(value)}</td>"
        rows += f"<tr><td>{dimension.value.title()}</td>{score_cell}<td>N/A</td></tr>"

    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"><title>NLR Benchmark Report</title>
    <style>
      body {{ font-family: Arial, sans-serif; margin: 40px; }}
      h1 {{ color: #1a365d; }}
      table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
      th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
      th {{ background: #edf2f7; }}
    </style>
    </head>
    <body>
      <h1>NLR Data Center Maturity Report</h1>
      <p><strong>Overall Score:</strong> {_fmt(diagnostic.get('overall_score'))}</p>
      <table>
        <thead><tr><th>Dimension</th><th>Score</th><th>Percentile</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </body>
    </html>
    """


@router.post(
    "/pdf",
    response_model=ReportPdfResponse,
)
@limiter.limit(RATE_LIMIT)
async def generate_pdf_report(
    request: Request,
    payload: ReportPdfRequest,
    pool: DbPool,
    settings: Settings = Depends(get_settings),
    pdf_client: PdfClientDep = None,  # type: ignore[assignment]
) -> ReportPdfResponse:
    if not settings.pdf_service_url:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=(
                "PDF generation is done client-side by the frontend "
                "(browser print); no PDF service is configured."
            ),
        )

    diagnostic = await benchmark_engine.get_diagnostic_by_id(pool, payload.diagnostic_id)
    if not diagnostic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnostic not found",
        )

    html = payload.html_content or _build_default_html(diagnostic)
    filename = f"nlr-report-{payload.diagnostic_id}.pdf"

    try:
        pdf_bytes = await pdf_client.generate_pdf(html, filename)
    except Exception as exc:
        logger.error(
            "pdf_generation_failed",
            diagnostic_id=payload.diagnostic_id,
            error=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="PDF generation failed",
        ) from exc

    return ReportPdfResponse(
        pdf_base64=base64.b64encode(pdf_bytes).decode(),
        filename=filename,
    )
