import base64

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.security import RATE_LIMIT, limiter
from app.deps import get_db, get_pdf_client
from app.models.schemas import ReportPdfRequest, ReportPdfResponse
from app.services import benchmark_engine
from app.services.pdf_client import PdfClient

router = APIRouter(prefix="/report", tags=["report"])


def _build_default_html(diagnostic: asyncpg.Record) -> str:
    """Genera el HTML del reporte a partir del registro v2 (benchmark_response + benchmark_result).

    NOTA: en v2 los scores viven en columnas fijas (visibility_score, ...),
    ya no en JSONB `dimension_scores` (modelo viejo). Este mapeo es el reflejo
    del esquema creado en schema-v2.sql.
    """
    dims = [
        ("visibility", "visibility_score"),
        ("friction", "friction_score"),
        ("latency", "latency_score"),
        ("quantification", "quantification_score"),
        ("blockers", "blockers_score"),
    ]
    rows = ""
    for label, column in dims:
        value = diagnostic.get(column)
        scores_html = f"<td>{value if value is not None else 'N/A'}</td>"
        rows += f"<tr><td>{label.title()}</td>{scores_html}<td>N/A</td></tr>"

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
      <p><strong>Overall Score:</strong> {diagnostic.get('overall_score', 'N/A')}</p>
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
    pool: asyncpg.Pool = Depends(get_db),
    pdf_client: PdfClient = Depends(get_pdf_client),
) -> ReportPdfResponse:
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
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"PDF generation failed: {exc}",
        ) from exc

    return ReportPdfResponse(
        pdf_base64=base64.b64encode(pdf_bytes).decode(),
        filename=filename,
    )
