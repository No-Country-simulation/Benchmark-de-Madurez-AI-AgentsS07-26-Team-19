import base64

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import get_db, get_pdf_client, rate_limit_dependency
from app.models.schemas import ReportPdfRequest, ReportPdfResponse
from app.services import benchmark_engine
from app.services.pdf_client import PdfClient

router = APIRouter(prefix="/report", tags=["report"])


def _build_default_html(diagnostic: asyncpg.Record) -> str:
    scores = diagnostic["dimension_scores"]
    rows = ""
    for dim, data in scores.items():
        rows += f"<tr><td>{dim.replace('_', ' ').title()}</td><td>{data['score']}</td><td>{data.get('percentile', 'N/A')}</td></tr>"

    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"><title>NLR Diagnostic Report</title>
    <style>
      body {{ font-family: Arial, sans-serif; margin: 40px; }}
      h1 {{ color: #1a365d; }}
      table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
      th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
      th {{ background: #edf2f7; }}
    </style>
    </head>
    <body>
      <h1>NLR Leadership Diagnostic Report</h1>
      <p><strong>Overall Score:</strong> {diagnostic['overall_score']}</p>
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
    dependencies=[Depends(rate_limit_dependency)],
)
async def generate_pdf_report(
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
