# Benchmark-de-Madurez-AI-AgentsS07-26-Team-19
Una startup de infraestructura de IA está construyendo el benchmark de madurez más completo de la industria sobre un problema crítico de los data centers modernos: la capacidad pagada y encendida que no produce nada porque las capas físicas y operativas del facility no se coordinan entre sí.

# NLR Diagnostic Backend

API FastAPI para el diagnóstico de liderazgo NLR. Incluye motor de benchmark, scoring en 5 dimensiones, cálculo de percentiles, rebalanceo dinámico y generación de reportes PDF vía microservicio Puppeteer.

La respuesta del diagnóstico es enriquecida (v2): perfil de fricción (dimensión dominante más débil), bandera de cuartil superior y los pesos vigentes público/real del rebalanceo. Incluye además análisis cualitativo IA en background (protocolo OpenAI-compatible: Ollama local o Hugging Face Inference Providers).

---

## Tabla de contenidos

1. [Requisitos previos](#requisitos-previos)
2. [Estructura del proyecto](#estructura-del-proyecto)
3. [Documentación](#documentación)
4. [Instalación local (sin Docker)](#instalación-local-sin-docker)
5. [Instalación con Docker Compose](#instalación-con-docker-compose)
6. [Configuración de la base de datos](#configuración-de-la-base-de-datos)
7. [Variables de entorno](#variables-de-entorno)
8. [Ejecutar el servidor](#ejecutar-el-servidor)
9. [Microservicio Puppeteer (PDF)](#microservicio-puppeteer-pdf)
10. [Endpoints de la API](#endpoints-de-la-api)
11. [Despliegue en la nube (Supabase + Vercel)](#despliegue-en-la-nube-supabase--vercel)
12. [Tests](#tests)
13. [Solución de problemas](#solución-de-problemas)

---

## Documentación

La documentación técnica completa vive en [`docs/`](../docs/README.md) (en español), con diagramas Mermaid:

| Documento | Contenido |
|---|---|
| [docs/architecture.md](../docs/architecture.md) | Arquitectura: C4 contexto y componentes, mapa de módulos, flujo de datos |
| [docs/api.md](../docs/api.md) | Referencia de endpoints, esquemas request/response, errores, rate limits |
| [docs/database-schema.md](../docs/database-schema.md) | Esquema v2: ERD, tablas, seed, mapeo de columnas |
| [docs/business-logic.md](../docs/business-logic.md) | Scoring, percentiles en vuelo, rebalanceo e idempotencia (con diagramas) |
| [docs/ai-analysis.md](../docs/ai-analysis.md) | Cliente IA, prompt, Ollama local vs HF, degradación |
| [docs/deployment.md](../docs/deployment.md) | Docker Compose, Supabase + Vercel, variables de entorno |

---

## Requisitos previos

### Opción A — Desarrollo local

| Herramienta    | Versión mínima | Verificar instalación      |
|----------------|----------------|----------------------------|
| Python         | 3.12+          | `python --version`         |
| pip            | 23+            | `pip --version`            |
| PostgreSQL     | 14+            | `psql --version`           |
| Node.js        | 20+            | `node --version`           |
| npm            | 10+            | `npm --version`            |
| Git            | cualquiera     | `git --version`            |

### Opción B — Solo Docker

| Herramienta    | Versión mínima | Verificar instalación      |
|----------------|----------------|----------------------------|
| Docker         | 24+            | `docker --version`         |
| Docker Compose | 2.20+          | `docker compose version`   |

---

## Estructura del proyecto

Monorepo con backend y frontend (React + Vite + TypeScript).

```
.
├── backend/                     # API FastAPI + servicios
│   ├── app/
│   │   ├── main.py              # FastAPI app, middleware, lifespan
│   │   ├── deps.py              # Dependencias compartidas (pool, clientes)
│   │   ├── core/
│   │   │   ├── config.py        # Settings (pydantic-settings)
│   │   │   ├── database.py      # asyncpg pool
│   │   │   ├── cache.py         # Cache TTL en proceso (stats/percentiles)
│   │   │   ├── dimensions.py    # Fuente única de las 5 dimensiones
│   │   │   ├── security.py      # Rate limiting, anon session
│   │   │   └── logging.py       # Structured logging
│   │   ├── models/
│   │   │   └── schemas.py       # Pydantic request/response
│   │   ├── services/
│   │   │   ├── benchmark_engine.py
│   │   │   ├── scoring.py
│   │   │   ├── percentiles.py
│   │   │   ├── rebalancing.py
│   │   │   ├── idempotency.py
│   │   │   ├── ai_client.py     # Cliente IA (protocolo OpenAI-compatible)
│   │   │   └── pdf_client.py
│   │   └── api/v1/
│   │       ├── diagnostic.py
│   │       ├── benchmark.py
│   │       └── report.py
│   ├── api/index.py             # Entrypoint ASGI de Vercel
│   ├── puppeteer-service/       # Microservicio Node + Puppeteer (PDF, solo local)
│   ├── scripts/
│   │   ├── schema-v2.sql        # DDL v2 (FKS, checks, TIMESTAMPTZ)
│   │   ├── seed-v2.sql          # Seed idempotente (15 preguntas + 20 filas públicas)
│   │   ├── nlr_feature_engineering.py
│   │   └── data/dataset.csv     # Dataset de telemetría NLR HPC PUE
│   ├── tests/                   # Suite pytest
│   ├── vercel.json
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── .env.example
├── docs/                        # Documentación técnica (español)
│   ├── README.md                # Índice de documentación
│   ├── architecture.md          # C4 contexto + componentes, flujo de datos
│   ├── api.md                   # Referencia de la API REST
│   ├── database-schema.md       # Esquema v2 + ERD
│   ├── business-logic.md        # Scoring, percentiles, rebalanceo, idempotencia
│   ├── ai-analysis.md           # Servicio de análisis IA
│   └── deployment.md            # Docker Compose, Supabase, Vercel
├── frontend/
│   └── benchmark-frontend/      # Frontend React + Vite + TypeScript (setup #40)
├── docker-compose.yml           # Orquestación de servicios
├── docker-compose.override.yml  # Override local (dev): puertos + servicio ai
└── README.md
```

---

## Instalación local (sin Docker)

Sigue estos pasos en orden si quieres correr todo en tu máquina.

### Paso 1 — Clonar y entrar al directorio

```bash
git clone <url-del-repositorio>
cd Benchmark-de-Madurez-AI-AgentsS07-26-Team-19/backend
```

### Paso 2 — Crear entorno virtual de Python

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Deberías ver `(.venv)` al inicio de tu prompt.

### Paso 3 — Instalar dependencias de Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Alternativa con `pyproject.toml`:

```bash
pip install -e ".[dev]"
```

### Paso 4 — Configurar variables de entorno

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Edita `.env` si necesitas cambiar credenciales de PostgreSQL u otros valores. Los defaults funcionan para desarrollo local.

### Paso 5 — Instalar y configurar PostgreSQL

#### 5.1 Instalar PostgreSQL

- **Windows:** Descarga el instalador desde [postgresql.org/download/windows](https://www.postgresql.org/download/windows/) y sigue el asistente. Recuerda la contraseña del usuario `postgres`.
- **macOS:** `brew install postgresql@16 && brew services start postgresql@16`
- **Ubuntu/Debian:** `sudo apt update && sudo apt install postgresql postgresql-contrib`

#### 5.2 Crear usuario y base de datos

Abre una terminal y conéctate como superusuario:

```bash
# Windows (ajusta la ruta si es necesario)
psql -U postgres

# macOS / Linux
sudo -u postgres psql
```

Ejecuta en el prompt de `psql`:

```sql
CREATE USER nlr WITH PASSWORD 'nlr_secret';
CREATE DATABASE nlr_diagnostic OWNER nlr;
GRANT ALL PRIVILEGES ON DATABASE nlr_diagnostic TO nlr;
\q
```

#### 5.3 Aplicar el schema v2

Desde el directorio `backend/`:

```bash
psql -U nlr -d nlr_diagnostic -f scripts/schema-v2.sql
```

Si te pide contraseña, usa `nlr_secret` (o la que hayas configurado).

#### 5.4 Seed del dataset

```bash
psql -U nlr -d nlr_diagnostic -f scripts/seed-v2.sql
```

Deberías ver:

```
preguntas        15
public_dataset   20
```

El seed es idempotente: re-ejecutarlo limpia (TRUNCATE) y recarga sin duplicar.

### Paso 6 — Instalar microservicio Puppeteer

```bash
cd puppeteer-service
npm install
cd ..
```

> **Nota Windows:** Puppeteer descargará Chromium (~150 MB). Si falla, instala las [dependencias de Puppeteer para Windows](https://pptr.dev/troubleshooting).

### Paso 7 — Levantar los servicios

Necesitas **3 terminales**:

**Terminal 1 — PostgreSQL** (si no corre como servicio):

```bash
# macOS
brew services start postgresql@16

# Linux
sudo systemctl start postgresql
```

**Terminal 2 — Puppeteer PDF service** (desde `backend/`):

```bash
cd puppeteer-service
npm start
# → Puppeteer PDF service listening on port 3001
```

**Terminal 3 — API FastAPI** (desde `backend/`):

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Paso 8 — Verificar que todo funciona

```bash
# Health check API
curl http://localhost:8000/health

# Health check Puppeteer
curl http://localhost:3001/health

# Preguntas del benchmark
curl http://localhost:8000/api/v1/benchmark/questions
```

Abre la documentación interactiva en: **http://localhost:8000/docs**

---

## Instalación con Docker Compose

La forma más rápida de levantar todo el stack.

### Paso 1 — Entrar al directorio raíz del repo

```bash
cd Benchmark-de-Madurez-AI-AgentsS07-26-Team-19
```

### Paso 2 — (Opcional) Configurar variables

```bash
cp backend/.env.example backend/.env
```

Docker Compose ya inyecta las variables necesarias en `docker-compose.yml`. Solo edita `backend/.env` si quieres personalizar.

### Paso 3 — Levantar servicios

```bash
docker compose up -d --build
```

Esto levanta:

| Servicio    | Puerto | Descripción                    |
|-------------|--------|--------------------------------|
| `db`        | 5432   | PostgreSQL 16                  |
| `api`       | 8000   | FastAPI                        |
| `puppeteer` | 3001   | Generación PDF                 |
| `ai`        | 11434  | Análisis IA (Ollama)           |

El schema v2 y el seed se aplican automáticamente al crear el contenedor de PostgreSQL (via `/docker-entrypoint-initdb.d/`), en orden: `01-schema.sql` → `02-seed.sql`.

> **Nota:** el servicio `ai` descarga el modelo (~1.1 GB) la primera vez que se
> levanta; puede tardar unos minutos. El análisis IA se genera en background,
> así que la API responde igual aunque el modelo aún se esté descargando.

### Paso 4 — Verificar

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/benchmark/questions
```

### Comandos útiles Docker

```bash
# Ver logs
docker compose logs -f api

# Detener todo
docker compose down

# Detener y borrar volúmenes (reset DB: schema + seed se re-aplican al arrancar)
docker compose down -v

# Reconstruir solo la API
docker compose up -d --build api
```

---

## Configuración de la base de datos

### Tablas principales (esquema v2)

| Tabla                   | Propósito                                                        |
|-------------------------|------------------------------------------------------------------|
| `question`              | Preguntas del diagnóstico por dimensión                           |
| `benchmark_response`    | Encuesta completada de forma anónima (una por sesión)             |
| `response_answer`       | Respuestas a cada pregunta con score normalizado (0-100)          |
| `benchmark_result`      | Scores por dimensión, overall y percentil de cada encuesta        |
| `public_dataset`        | Datos públicos de referencia (20 filas en el seed)                |
| `rebalance_config`      | Pesos vigentes público/real (fila única)                          |

### Las 5 dimensiones

| Dimensión | Descripción |
|-----------|-------------|
| `visibility` | Vista unificada de energía, cooling y workloads |
| `friction` | Identificación de la interfaz donde se pierde más capacidad |
| `latency` | Velocidad de ajuste de cooling y energía ante cambios de workload |
| `quantification` | Conocimiento de la stranded capacity propia |
| `blockers` | Obstáculos organizacionales o técnicos que impiden la resolución |

### Conexión manual

```bash
psql -h localhost -U nlr -d nlr_diagnostic
```

### Reset completo de la DB (local)

```bash
psql -U postgres -c "DROP DATABASE IF EXISTS nlr_diagnostic;"
psql -U postgres -c "CREATE DATABASE nlr_diagnostic OWNER nlr;"
psql -U nlr -d nlr_diagnostic -f scripts/schema-v2.sql
psql -U nlr -d nlr_diagnostic -f scripts/seed-v2.sql
```

---

## Variables de entorno

Copia `backend/.env.example` a `backend/.env`. Referencia completa:

| Variable                      | Default                  | Descripción                          |
|-------------------------------|--------------------------|--------------------------------------|
| `ENVIRONMENT`                 | `development`            | Entorno de ejecución                 |
| `DEBUG`                       | `false`                  | Habilita `/docs` y modo debug        |
| `POSTGRES_HOST`               | `localhost`              | Host de PostgreSQL                   |
| `POSTGRES_PORT`               | `5432`                   | Puerto de PostgreSQL                 |
| `POSTGRES_USER`               | `nlr`                    | Usuario de PostgreSQL                |
| `POSTGRES_PASSWORD`           | `nlr_secret`             | Contraseña de PostgreSQL             |
| `POSTGRES_DB`                 | `nlr_diagnostic`         | Nombre de la base de datos           |
| `POSTGRES_MIN_POOL_SIZE`      | `0`                      | Conexiones mínimas del pool (serverless: 0) |
| `POSTGRES_MAX_POOL_SIZE`      | `3`                      | Conexiones máximas del pool (serverless: 2-3) |
| `POSTGRES_SSL`                | `false`                  | `true` al conectar a Supabase (exige TLS) |
| `RATE_LIMIT_REQUESTS`         | `60`                     | Requests permitidos por ventana      |
| `RATE_LIMIT_WINDOW_SECONDS`   | `60`                     | Duración de la ventana (segundos)    |
| `TRUST_PROXY_HEADERS`         | `false`                  | `true` en Vercel (proxy inverso)     |
| `CORS_ORIGINS`                | `["http://localhost:3000"]` | Orígenes permitidos para CORS    |
| `PDF_SERVICE_URL`             | *(vacío)*                | Puppeteer es legacy/local; vacío en producción (el front genera el PDF) |
| `PDF_SERVICE_TIMEOUT_SECONDS` | `30`                     | Timeout para generación de PDF       |
| `AI_SERVICE_URL`              | `http://localhost:11434` | URL del servicio de IA (Ollama local o `https://router.huggingface.co`) |
| `HF_TOKEN`                    | *(vacío)*                | Token HF Read para el router de Inference Providers |
| `AI_MODEL`                    | `hf.co/mradermacher/NeuralQwen-2.5-1.5B-Spanish-GGUF:Q4_K_M` | Modelo IA (default local); en nube suele ser `meta-llama/Llama-3.3-70B-Instruct` |
| `AI_TIMEOUT_SECONDS`          | `120`                    | Timeout para el análisis IA          |
| `AI_MAX_TOKENS`               | `512`                    | Límite de tokens del análisis        |
| `LOG_LEVEL`                   | `INFO`                   | Nivel de logging                     |
| `LOG_JSON`                    | `false`                  | Logging en formato JSON              |

---

## Ejecutar el servidor

### Desarrollo (con hot-reload)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Producción

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Análisis IA automático

Genera el `ai_analysis` de cada diagnóstico (Markdown en español: resumen,
fortalezas, áreas de mejora y recomendaciones). El cliente habla **protocolo
OpenAI-compatible** (`/v1/chat/completions`), así que funciona contra:

- **Ollama local** (dev): `AI_SERVICE_URL=http://localhost:11434` con el modelo
  `NeuralQwen-2.5-1.5B-Spanish` (GGUF Q4_K_M, ~1.1 GB) y `HF_TOKEN` vacío.
- **Hugging Face Inference Providers** (nube): `AI_SERVICE_URL=https://router.huggingface.co`,
  `HF_TOKEN=<token read hf_...>` y `AI_MODEL=meta-llama/Llama-3.3-70B-Instruct`.

- El análisis se genera como `BackgroundTask` tras cada diagnóstico nuevo
  (no bloquea el POST); si el servicio no está disponible, se loguea y el
  `ai_analysis` queda `NULL` sin romper el flujo.
- Se lee con `GET /api/v1/diagnostic/{id}` (campo `ai_analysis`) y el estado del
  servicio con `GET /health/ai`.

Verificar en local (Ollama):

```bash
# health del servicio (Ollama)
curl http://localhost:11434/v1/models

# generar análisis manualmente
curl -X POST http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"hf.co/mradermacher/NeuralQwen-2.5-1.5B-Spanish-GGUF:Q4_K_M","messages":[{"role":"user","content":"Resumen en 1 frase."}],"max_tokens":100}'
```

---

## Microservicio Puppeteer (PDF) — LEGACY / solo local

> **En producción el PDF lo genera el frontend** (impresión del navegador sobre
> el HTML del reporte), así el backend no depende de un contenedor Puppeteer
> que Vercel no puede ejecutar. Este microservicio queda solo para desarrollo
> local; con `PDF_SERVICE_URL` vacío, `POST /report/pdf` responde **501**.

Servicio Node.js independiente que convierte HTML a PDF.

### Instalación

```bash
cd puppeteer-service
npm install
```

### Ejecución

```bash
npm start          # producción
npm run dev        # con --watch (Node 20+)
```

### Probar directamente

```bash
curl -X POST http://localhost:3001/generate \
  -H "Content-Type: application/json" \
  -d '{"html":"<h1>Test</h1>","filename":"test.pdf"}'
```

---

## Despliegue en la nube (Supabase + Vercel)

> **Estado actual:** la API ya está **desplegada y operativa** en este stack
> (Vercel serverless + Supabase pooler + Hugging Face Inference Providers).
> El PDF se genera en el frontend; `puppeteer-service` no está desplegado.

Stack objetivo, 100% en free tiers:

| Pieza        | Servicio                          | URL de ejemplo |
|--------------|-----------------------------------|----------------|
| Base de datos| Supabase (Postgres + pooler)      | `db.<ref>.supabase.co:6543` |
| Backend API  | Vercel (Función ASGI de FastAPI)  | `https://tu-app.vercel.app` |
| Modelo IA    | Hugging Face Inference Providers | `https://router.huggingface.co` |
| Reporte PDF  | **Frontend** (impresión navegador)| — (sin servicio en la nube) |

> Notas honestas:
> - El rate limit (`slowapi`) en Vercel es **por instancia**, no global; a nivel
>   de demo es aceptable. Un proxy externo (Cloudflare, etc.) podría dar uno global.
> - La primera llamada a la IA tras un *cold start* del HF Space puede tardar
>   60–120s+ en CPU. El `BackgroundTask` degrada con gracia: si el servicio no
>   responde, el `ai_analysis` queda `NULL` y el diagnóstico no falla.

### Paso 1 — Base de datos en Supabase (free)

1. Crear un proyecto en https://supabase.com (plan Free).
2. En **SQL Editor**, ejecutar en orden:
   ```sql
   -- 1) DDL
   backend/scripts/schema-v2.sql

   -- 2) Seed (dataset real de telemetría NLR + preguntas)
   backend/scripts/seed-v2.sql
   ```
   Compatibilidad ya verificada: `pgcrypto`, FKs, advisory locks y
   `TRUNCATE ... CASCADE` funcionan en Supabase.
3. Copiar la **connection string del pooler** (modo transaction):
   `Settings → Database → Connection string → Pooler` → `URI`.
   Formato:
   `postgresql://postgres.<ref>:<PASSWORD>@aws-0-<region>.pooler.supabase.com:6543/postgres`

### Paso 2 — Modelo IA en Hugging Face Inference Providers (free)

> Los **Spaces Docker/Gradio** hoy requieren plan PRO; la alternativa gratis es la
> **Inference API serverless** (`https://router.huggingface.co`), compatible
> OpenAI. No hay que desplegar nada: solo un token.

1. Crear un **token Read** en https://huggingface.co/settings/tokens (empieza con `hf_`).
2. En Vercel cargar como env vars:
   ```
   AI_SERVICE_URL=https://router.huggingface.co
   HF_TOKEN=<tu-token-hf_...>
   AI_MODEL=meta-llama/Llama-3.3-70B-Instruct
   AI_TIMEOUT_SECONDS=120
   AI_MAX_TOKENS=512
   ```
3. Verificar:
   ```bash
   curl -H "Authorization: Bearer $HF_TOKEN" https://router.huggingface.co/v1/models
   # y el estado del análisis con el backend desplegado:
   curl https://<tu-backend>.vercel.app/health/ai
   ```
4. (Opcional) Si querés el modelo local en vez del router, corré Ollama y apuntá
   `AI_SERVICE_URL=http://localhost:11434` con `HF_TOKEN` vacío.

### Paso 3 — Backend en Vercel (free)

El repo ya trae `api/index.py` (handler ASGI) y `vercel.json` (`maxDuration` 300s).

1. En https://vercel.com → **Add New → Project** → importar el repo.
2. **Root Directory:** `backend` (el proyecto a desplegar es el backend).
3. Framework Preset: **Other** (Vercel detecta el entrypoint `api/index.py`).
4. Setear las **variables de entorno** (Environment Variables):

   | Variable | Valor |
   |----------|-------|
   | `ENVIRONMENT` | `production` |
   | `DEBUG` | `false` |
   | `LOG_JSON` | `true` |
   | `TRUST_PROXY_HEADERS` | `true` |
   | `CORS_ORIGINS` | `["https://tu-front.vercel.app"]` (ajustar) |
   | `POSTGRES_HOST` | `aws-0-<region>.pooler.supabase.com` |
   | `POSTGRES_PORT` | `6543` |
   | `POSTGRES_USER` | `postgres.<project-ref>` |
   | `POSTGRES_PASSWORD` | *(password del proyecto)* |
   | `POSTGRES_DB` | `postgres` |
   | `POSTGRES_SSL` | `true` |
   | `POSTGRES_CA_CERT` | contenido PEM de `prod-ca-2021.crt` (`Settings → Database → SSL Configuration`) — habilita verify-full |
   | `AI_SERVICE_URL` | `https://router.huggingface.co` |
   | `HF_TOKEN` | *(token Read hf_...)* |
   | `AI_MODEL` | `meta-llama/Llama-3.3-70B-Instruct` |
   | `AI_TIMEOUT_SECONDS` | `120` |
   | `PDF_SERVICE_URL` | *(vacío — el front genera el PDF)* |

5. **Deploy**.
6. Verificar:
   ```bash
   curl https://tu-app.vercel.app/health
   curl https://tu-app.vercel.app/api/v1/benchmark/questions
   ```

> `POSTGRES_HOST` es el host del **pooler** (no `db.<ref>.supabase.co:5432`).
> El puerto 6543 (modo transaction) es el que sobrevive a serverless; el pool
> se crea por instancia con `max_size` pequeño (`statement_cache_size=0`
> ya está seteado en `core/database.py`).

#### Alternativa oficial: CLI de Vercel

Igual de válida que el dashboard; esta es la vía que recomienda la skill
oficial `deploy-to-vercel` (vercel-labs). El repo ya tiene remote GitHub, así
que el flujo queda:

```bash
# 1) Instalar y autenticar (una sola vez)
npm install -g vercel
vercel login

# 2) Vincular el repo a un proyecto de Vercel (root = backend/)
cd backend
vercel link --repo        # usa el remote GitHub (mejor que `vercel link` a secas)

# 3) Deploy de prueba (preview, no producción)
vercel deploy . -y --no-wait

# 4) Producción (cuando esté todo verificado)
vercel deploy . --prod -y --no-wait
```

- Las variables de entorno se setean una vez con `vercel env add <VARIABLE>`
  (o en el dashboard: *Settings → Environment Variables*).
- Una vez linkeado, **cada `git push`** a la rama de producción dispara un
  deploy automático; los branches generan previews.
- `--no-wait` devuelve la URL al instante; verificá el build con
  `vercel inspect <url>`.

### Paso 4 — Reporte PDF

El frontend genera el PDF (botón *Imprimir / Guardar como PDF* sobre el HTML del
reporte). Con `PDF_SERVICE_URL` vacío, `POST /report/pdf` responde 501 con un
mensaje que apunta a esa estrategia. `puppeteer-service` queda solo para dev.

### Rollback / deps

- **Reset DB en Supabase:** re-ejecutar `schema-v2.sql` + `seed-v2.sql` en el
  SQL Editor (el seed es idempotente: `TRUNCATE ... CASCADE` + `INSERT`).
- **Re-deploy en Vercel:** cada push a la rama configurada re-despliega solo.

---

## Endpoints de la API

Base URL: `http://localhost:8000/api/v1`

### Diagnostic

| Método | Ruta                        | Descripción                    |
|--------|-----------------------------|--------------------------------|
| POST   | `/diagnostic`               | Enviar respuestas del test     |
| GET    | `/diagnostic/{id}`          | Obtener resultado por ID       |

**Ejemplo POST /diagnostic:**

```bash
curl -X POST http://localhost:8000/api/v1/diagnostic \
  -H "Content-Type: application/json" \
  -d '{
    "answers": [
      {"question_id": 1, "value": 4},
      {"question_id": 2, "value": 5},
      {"question_id": 3, "value": 3}
    ]
  }'
```

> Las `question_id` son enteros (SERIAL de la tabla `question`). Usa
> `GET /benchmark/questions` para obtener los ids vigentes.

### Benchmark

| Método | Ruta                           | Descripción                          |
|--------|--------------------------------|--------------------------------------|
| GET    | `/benchmark/questions`         | Listar preguntas                     |
| GET    | `/benchmark/stats`             | Estadísticas por dimensión           |
| GET    | `/benchmark/percentiles`       | Tabla de percentiles                 |
| POST   | `/benchmark/percentiles/lookup`| Buscar percentil de un score         |
| GET    | `/benchmark/weights`           | Pesos actuales público/real          |

### Report

| Método | Ruta              | Descripción                    |
|--------|-------------------|--------------------------------|
| POST   | `/report/pdf`     | Generar reporte PDF            |

### Health

| Método | Ruta      | Descripción    |
|--------|-----------|----------------|
| GET    | `/health` | Estado del API |
| GET    | `/health/ai` | Estado del servicio de análisis IA (probe a `/v1/models`) |

---

## Tests

```bash
cd backend
pytest

# Con cobertura
pytest --cov=app --cov-report=term-missing

# Un archivo específico
pytest tests/test_scoring.py -v
```

---

## Solución de problemas

### `Connection refused` al conectar a PostgreSQL

1. Verifica que PostgreSQL esté corriendo: `pg_isready -h localhost -p 5432`
2. Confirma credenciales en `.env`
3. En Docker: `docker compose ps` y revisa que `db` esté `healthy`

### `Database pool is not initialized`

La API se levantó pero no pudo conectar a la DB. Revisa logs:

```bash
# Local
uvicorn app.main:app --reload 2>&1 | head -20

# Docker
docker compose logs api
```

### Puppeteer falla al generar PDF

1. Verifica que el servicio esté corriendo: `curl http://localhost:3001/health`
2. En Docker, el contenedor necesita `shm_size: 1gb` (ya configurado)
3. En Linux sin Docker, instala dependencias: `sudo apt install chromium-browser`

### `Rate limit exceeded`

Espera 60 segundos o ajusta `RATE_LIMIT_REQUESTS` / `RATE_LIMIT_WINDOW_SECONDS` en `.env`.

> Nota: el límite usa slowapi con almacenamiento en memoria (`memory://`), válido para
> un proceso/servidor. Con varias instancias de uvicorn, cada worker tiene su propio
> contador; para un límite global consistente migrar a un almacén compartido (Redis).

### Error al importar módulos (`ModuleNotFoundError: app`)

Asegúrate de ejecutar desde el directorio `backend/` y que `PYTHONPATH` incluya el directorio raíz:

```bash
# Windows PowerShell
$env:PYTHONPATH = "."
uvicorn app.main:app --reload

# macOS / Linux
PYTHONPATH=. uvicorn app.main:app --reload
```

### Reset completo con Docker

```bash
docker compose down -v
docker compose up -d --build
```

El volumen se recrea vacío y el schema + seed v2 se re-aplican automáticamente al arrancar.

---

## Licencia

Proyecto interno — No Country.
