"""HTTP client for the Puppeteer PDF microservice."""

import base64

import httpx

from app.core.config import Settings


class PdfClient:
    def __init__(self, settings: Settings) -> None:
        self.base_url = settings.pdf_service_url.rstrip("/")
        self.timeout = settings.pdf_service_timeout_seconds

    async def generate_pdf(
        self,
        html: str,
        filename: str = "report.pdf",
    ) -> bytes:
        url = f"{self.base_url}/generate"
        payload = {"html": html, "filename": filename}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        if "pdf_base64" in data:
            return base64.b64decode(data["pdf_base64"])
        if "pdf" in data:
            return base64.b64decode(data["pdf"])

        raise ValueError("PDF service returned unexpected response format")
