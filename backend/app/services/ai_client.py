"""HTTP client for the local AI analysis service (Ollama).

Genera el análisis cualitativo (``ai_analysis``) de un diagnóstico a partir de
los scores por dimensión. Usa un modelo local en español
(NeuralQwen-2.5-1.5B-Spanish) servido por Ollama, por lo que los datos nunca
salen del despliegue.

Prompt: se le pasa un bloque JSON con los scores + contexto fijo de las 5
dimensiones del benchmark, y el modelo devuelve el análisis en Markdown.
"""

import json
from collections.abc import Mapping

import httpx

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """Eres un analista senior de madurez en data centers.
Recibes los scores (0-100) de las 5 dimensiones de un diagnóstico operativo:
- visibility: vista unificada de energía, cooling y workloads
- friction: identificación de la interfaz donde se pierde más capacidad
- latency: velocidad de ajuste de cooling y energía ante cambios de workload
- quantification: conocimiento de la stranded capacity propia
- blockers: obstáculos organizacionales o técnicos que impiden la resolución

Genera un análisis breve en español (máximo 400 palabras) en formato Markdown con:
## Resumen
## Fortalezas
## Áreas de mejora
## Recomendaciones (3 accionables)
Sé concreto y usa los números del diagnóstico. No inventes datos."""


class AiClient:
    def __init__(self, settings: Settings) -> None:
        self.base_url = settings.ai_service_url.rstrip("/")
        self.model = settings.ai_model
        self.timeout = settings.ai_timeout_seconds
        self.max_tokens = settings.ai_max_tokens

    async def analyze(
        self,
        dimension_scores: Mapping[str, float],
        overall_score: float,
    ) -> str:
        """Genera el análisis cualitativo del diagnóstico y devuelve el Markdown."""
        payload = {
            "scores": {k: round(v, 1) for k, v in dimension_scores.items()},
            "overall_score": round(overall_score, 1),
        }
        user_prompt = (
            f"{json.dumps(payload, ensure_ascii=False)}\n\n"
            "Genera el análisis del diagnóstico según las instrucciones del sistema."
        )

        body = {
            "model": self.model,
            "system": SYSTEM_PROMPT,
            "prompt": user_prompt,
            "stream": False,
            "options": {
                "num_predict": self.max_tokens,
                "temperature": 0.4,
                "top_p": 0.9,
            },
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/api/generate", json=body)
            response.raise_for_status()
            data = response.json()

        text = (data.get("response") or "").strip()
        if not text:
            raise ValueError("AI service returned an empty analysis")
        return text

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except httpx.HTTPError as exc:
            logger.warning("ai_service_unavailable", error=str(exc))
            return False
