"""Tests for the AI analysis client (app/services/ai_client.py)."""

import httpx
import pytest
from pytest_httpx import HTTPXMock

from app.core.config import Settings
from app.services.ai_client import SYSTEM_PROMPT, AiClient


def _client() -> AiClient:
    settings = Settings(ai_service_url="http://ai:11434")
    return AiClient(settings)


@pytest.mark.asyncio
async def test_analyze_returns_clean_text(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="http://ai:11434/api/generate",
        method="POST",
        json={"response": "## Resumen\nTexto de prueba\n"},
    )

    text = await _client().analyze(
        {"visibility": 80.0, "friction": 70.0}, overall_score=75.0
    )

    assert text == "## Resumen\nTexto de prueba"


@pytest.mark.asyncio
async def test_analyze_sends_scores_and_system_prompt(httpx_mock: HTTPXMock) -> None:
    captured: dict = {}

    def _handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = request.content
        return httpx.Response(200, json={"response": "ok"})

    httpx_mock.add_callback(_handler, url="http://ai:11434/api/generate")

    await _client().analyze({"visibility": 80.5}, overall_score=80.5)

    body = captured["body"].decode()
    assert "visibility" in body
    assert "80.5" in body
    assert SYSTEM_PROMPT[:50] in body


@pytest.mark.asyncio
async def test_analyze_raises_on_empty_response(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="http://ai:11434/api/generate", method="POST", json={"response": ""}
    )

    with pytest.raises(ValueError, match="empty analysis"):
        await _client().analyze({"visibility": 80.0}, overall_score=80.0)


@pytest.mark.asyncio
async def test_analyze_raises_on_http_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="http://ai:11434/api/generate", method="POST", status_code=500
    )

    with pytest.raises(httpx.HTTPStatusError):
        await _client().analyze({"visibility": 80.0}, overall_score=80.0)


@pytest.mark.asyncio
async def test_health_check_ok(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url="http://ai:11434/api/tags", method="GET")
    assert await _client().health_check() is True


@pytest.mark.asyncio
async def test_health_check_false_on_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_exception(httpx.ConnectError("down"), url="http://ai:11434/api/tags")
    assert await _client().health_check() is False
