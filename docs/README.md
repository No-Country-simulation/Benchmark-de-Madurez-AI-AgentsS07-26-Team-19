# Backend de Diagnóstico NLR — Documentación

Centro de documentación técnica del **Backend de Diagnóstico NLR**: una API
FastAPI que ejecuta un benchmark de madurez de agentes de IA para data centers
modernos en 5 dimensiones, con cálculo de percentiles en vuelo, rebalanceo
dinámico entre el dataset público inicial y las respuestas reales, persistencia
idempotente de diagnósticos, análisis IA y generación de reportes PDF.

---

## Índice de documentación

| Documento | Contenido |
|---|---|
| [architecture.md](./architecture.md) | Arquitectura: C4 contexto y componentes, mapa de módulos, flujo de datos |
| [api.md](./api.md) | Referencia de la API REST: endpoints, esquemas, errores, rate limits |
| [database-schema.md](./database-schema.md) | Esquema v2 de PostgreSQL: ERD, tablas, seed, mapeo de columnas |
| [business-logic.md](./business-logic.md) | Lógica de negocio: scoring, percentiles, rebalanceo, idempotencia |
| [ai-analysis.md](./ai-analysis.md) | Servicio de análisis IA: cliente compatible OpenAI, prompt, local/nube |
| [deployment.md](./deployment.md) | Despliegue: Docker Compose, Supabase, Vercel, variables de entorno |

---

## Estructura del repositorio

```text
.
├── backend/                     # Backend FastAPI + servicios
│   ├── app/
│   │   ├── main.py              # App FastAPI, lifespan, middleware
│   │   ├── deps.py              # Dependencias compartidas (pool, clientes)
│   │   ├── core/                # config, database, dimensions, security, logging, cache
│   │   ├── models/schemas.py    # Modelos Pydantic de request/response
│   │   ├── services/            # benchmark_engine, scoring, percentiles, rebalancing, idempotency, ai_client, pdf_client
│   │   └── api/v1/              # Routers: diagnostic, benchmark, report
│   ├── api/index.py             # Entrypoint ASGI de Vercel
│   ├── puppeteer-service/       # Node.js + Puppeteer HTML→PDF (solo local)
│   ├── scripts/                 # Utilidades de base de datos y ciencia de datos
│   │   ├── schema-v2.sql        # DDL del esquema v2
│   │   ├── seed-v2.sql          # Datos semilla del dataset público
│   │   ├── nlr_feature_engineering.py  # Feature engineering del dataset NLR
│   │   └── data/
│   │       └── dataset.csv      # Dataset público de referencia
│   ├── tests/                   # Suite de pytest
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── .env.example
├── docs/                        # Este centro de documentación
├── docker-compose.yml           # Servicios: db + api + puppeteer
├── docker-compose.override.yml  # Override de dev local: puertos + servicio ai (Ollama)
└── README.md
```

## Datos rápidos

- **Estado actual**: la API ya está **desplegada** (Vercel serverless + Supabase Postgres + Hugging Face Inference Providers).
- **Stack**: Python 3.12, FastAPI, asyncpg, PostgreSQL 16, Pydantic v2, pydantic-settings, structlog, slowapi, httpx.
- **5 dimensiones**: `visibility`, `friction`, `latency`, `quantification`, `blockers`.
- **Prefijo de API**: `/api/v1`.
- **Docs interactivos**: `/docs` (protegidos con HTTP Basic Auth en producción si `SWAGGER_PASSWORD` está definido).
- **6 tablas v2**: `question`, `benchmark_response`, `response_answer`, `benchmark_result`, `public_dataset`, `rebalance_config`.