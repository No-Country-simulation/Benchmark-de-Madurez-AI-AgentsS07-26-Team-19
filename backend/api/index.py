"""Entrypoint de Vercel para el backend FastAPI.

Vercel detecta el objeto ``app`` (ASGI) y lo sirve como una única función
serverless. El pool de la base de datos se crea/cierra vía el lifespan de
FastAPI en cada instancia (Fluid Compute); los límites de duración están en
``vercel.json``.
"""

from app.main import app  # noqa: F401  # handler ASGI que expone Vercel
