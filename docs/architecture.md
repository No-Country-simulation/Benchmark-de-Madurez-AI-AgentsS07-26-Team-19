# Arquitectura

Este documento describe la arquitectura del **Backend de Diagnóstico NLR** a
nivel de contexto del sistema y de componentes, además del flujo de datos y la
topología de ejecución/despliegue.

---

## Contexto del sistema

```mermaid
C4Context
    title Contexto del sistema — Backend de Diagnóstico NLR

    Person(usuario, "Operador / Cliente", "Responde el benchmark, consulta resultados y ve reportes")
    System(api, "API de Diagnóstico NLR", "Backend FastAPI: scoring, percentiles en vuelo, rebalanceo dinámico, persistencia idempotente, análisis IA, reportes PDF")

    System_Ext(pg, "PostgreSQL 16", "Esquema v2: question, benchmark_response, response_answer, benchmark_result, public_dataset, rebalance_config")
    System_Ext(ai, "Servicio IA", "Compatible OpenAI /v1/chat/completions (Ollama local o Hugging Face Inference Providers)")
    System_Ext(pdf, "Servicio PDF Puppeteer", "Generación de HTML a PDF (Node.js, solo local/legacy)")

    Rel(usuario, api, "HTTP /api/v1")
    Rel(api, pg, "pool asyncpg")
    Rel(api, ai, "HTTP (BackgroundTask)")
    Rel(api, pdf, "HTTP /generate (opcional)")
```

---

## Mapa de componentes (backend/app)

La aplicación FastAPI se divide en cuatro capas: `core` (infraestructura),
`models` (esquemas), `services` (lógica de negocio / repositorios) y `api/v1`
(controladores HTTP). `main.py` conecta todo.

```mermaid
flowchart TD
    subgraph app["backend/app"]
        MAIN["main.py<br/>App FastAPI · lifespan · CORS · docs Basic Auth · rate limit"]
        DEPS["deps.py<br/>get_db · get_ai_client · get_pdf_client"]

        subgraph api["api/v1"]
            D["diagnostic.py<br/>POST /diagnostic · GET /diagnostic/{id}"]
            B["benchmark.py<br/>questions · stats · percentiles · weights"]
            R["report.py<br/>POST /report/pdf"]
        end

        subgraph core["core"]
            CFG["config.py<br/>pydantic-settings (env)"]
            DB["database.py<br/>pool asyncpg"]
            DIM["dimensions.py<br/>5 dimensiones · columnas · normalize"]
            SEC["security.py<br/>limiter slowapi · sesión anónima · IP cliente"]
            LOG["logging.py<br/>structlog"]
            CACHE["cache.py<br/>ttl_cache (en proceso)"]
        end

        subgraph services["services"]
            BE["benchmark_engine.py<br/>questions · save (idempotente) · get by id"]
            SC["scoring.py<br/>scores dimensiones + overall"]
            PC["percentiles.py<br/>weighted_merge · calculate_percentile"]
            RB["rebalancing.py<br/>compute_weights · run_rebalancing"]
            ID["idempotency.py<br/>fingerprint respuestas (SHA-256)"]
            AI["ai_client.py<br/>cliente compatible OpenAI"]
            PDF["pdf_client.py<br/>cliente HTTP a Puppeteer"]
        end

        MAIN --> D
        MAIN --> B
        MAIN --> R
        D --> BE
        D --> SC
        D --> PC
        D --> RB
        D --> ID
        D --> AI
        R --> BE
        R --> PDF
        B --> BE
        B --> PC
        B --> RB
        BE --> DB
        SC --> DIM
        PC --> DIM
        PC --> CACHE
        AI --> CFG
        PDF --> CFG
        RB --> DB
    end

    PG[("PostgreSQL 16<br/>schema v2")]

    DEPS -. "pool para inyección" .-> D
    DEPS -. "pool para inyección" .-> B
    DEPS -. "pool para inyección" .-> R
    DB --> PG
```

---

## Ejecución y flujo de datos

Propiedades clave de la ejecución:

- **Lifespan** (`app/main.py`): inicializa el logging estructurado y el pool
  asyncpg al arrancar; cierra el pool al apagar.
- **Pool de base de datos** (`core/database.py`): se inicializa en el
  `lifespan` de FastAPI al arrancar la app (en serverless, esto ocurre en el
  cold start de cada instancia). Pool pequeño
  (`max_size=3`) porque cada instancia serverless abre el suyo.
  `statement_cache_size=0` para compatibilidad con el pooler transaction de Supabase.
- **Flujo de request**: HTTP → router (`api/v1`) → services → PostgreSQL. Las
  llamadas externas (IA, PDF) se hacen por HTTP con `httpx`.
- **POST /diagnostic** es asíncrono: la respuesta se devuelve de inmediato y los
  efectos secundarios (rebalanceo + análisis IA) corren como `BackgroundTask`.
- **Cliente IA** (`services/ai_client.py`): corre exclusivamente como
  `BackgroundTask`, nunca en el path crítico del request. Esto garantiza que
  una latencia o fallo del servicio IA no afecte el tiempo de respuesta del
  endpoint.
- **Cache**: `_fetch_dimension_stats` y `_load_blended_scores` son caches TTL en
  proceso de 30s (por instancia, no distribuido).

El flujo completo del diagnóstico está en [business-logic.md](./business-logic.md).