# Benchmark-de-Madurez-AI-AgentsS07-26-Team-19
Una startup de infraestructura de IA está construyendo el benchmark de madurez más completo de la industria sobre un problema crítico de los data centers modernos: la capacidad pagada y encendida que no produce nada porque las capas físicas y operativas del facility no se coordinan entre sí.

# NLR Diagnostic Backend

API FastAPI para el diagnóstico de liderazgo NLR. Incluye motor de benchmark, scoring en 5 dimensiones, cálculo de percentiles, rebalanceo dinámico y generación de reportes PDF vía microservicio Puppeteer.

---

## Tabla de contenidos

1. [Requisitos previos](#requisitos-previos)
2. [Estructura del proyecto](#estructura-del-proyecto)
3. [Instalación local (sin Docker)](#instalación-local-sin-docker)
4. [Instalación con Docker Compose](#instalación-con-docker-compose)
5. [Configuración de la base de datos](#configuración-de-la-base-de-datos)
6. [Variables de entorno](#variables-de-entorno)
7. [Ejecutar el servidor](#ejecutar-el-servidor)
8. [Microservicio Puppeteer (PDF)](#microservicio-puppeteer-pdf)
9. [Endpoints de la API](#endpoints-de-la-api)
10. [Tests](#tests)
11. [Solución de problemas](#solución-de-problemas)

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

Monorepo con backend y frontend (este último se agregará en el mismo repositorio):

```
.
├── backend/                     # API FastAPI + servicios
│   ├── app/
│   │   ├── main.py              # FastAPI app, middleware, lifespan
│   │   ├── core/
│   │   │   ├── config.py        # Settings (pydantic-settings)
│   │   │   ├── database.py      # asyncpg pool
│   │   │   ├── security.py      # Rate limiting, anon session
│   │   │   └── logging.py       # Structured logging
│   │   ├── models/
│   │   │   └── schemas.py       # Pydantic request/response
│   │   ├── services/
│   │   │   ├── benchmark_engine.py
│   │   │   ├── scoring.py
│   │   │   ├── percentiles.py
│   │   │   ├── rebalancing.py
│   │   │   └── pdf_client.py
│   │   ├── api/v1/
│   │   │   ├── diagnostic.py
│   │   │   ├── benchmark.py
│   │   │   └── report.py
│   │   └── deps.py
│   ├── puppeteer-service/       # Microservicio Node + Puppeteer
│   ├── scripts/
│   │   ├── schema.sql
│   │   └── seed_nlr.py
│   ├── tests/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── .env.example
├── frontend/                    # (próximamente)
├── docker-compose.yml           # Orquestación de servicios
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

#### 5.3 Aplicar el schema

Desde el directorio `backend/`:

```bash
psql -U nlr -d nlr_diagnostic -f scripts/schema.sql
```

Si te pide contraseña, usa `nlr_secret` (o la que hayas configurado).

#### 5.4 Seed del dataset NLR

Con el entorno virtual activo:

```bash
python scripts/seed_nlr.py
```

Deberías ver:

```
Seeding NLR dataset...
  ✓ Seeded 10 questions
  ✓ Seeded 1000 benchmark scores
  ✓ Seeded percentile buckets
Done.
```

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

El schema SQL se aplica automáticamente al crear el contenedor de PostgreSQL (via `/docker-entrypoint-initdb.d/`).

### Paso 4 — Seed del dataset

```bash
docker compose --profile seed run --rm seed
```

### Paso 5 — Verificar

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

# Detener y borrar volúmenes (reset DB)
docker compose down -v

# Reconstruir solo la API
docker compose up -d --build api
```

---

## Configuración de la base de datos

### Tablas principales

| Tabla                   | Propósito                                                        |
|-------------------------|------------------------------------------------------------------|
| `benchmark_questions`   | Preguntas del diagnóstico por dimensión                          |
| `benchmark_scores`      | Scores de la población de referencia (pública + real)            |
| `benchmark_percentiles` | Buckets precalculados de percentiles                             |
| `benchmark_weights`     | Pesos dinámicos por dimensión (actualizados por rebalanceo)      |
| `rebalancing_config`    | Historial de pesos público/real por conteo de respuestas reales  |
| `diagnostics`           | Resultados de diagnósticos anónimos de operadores                |

### Las 5 dimensiones

| Dimensión | Descripción |
|-----------|-------------|
| `visibilidad_cross_layer` | Vista unificada de energía, cooling y workloads |
| `atribucion_friccion` | Identificación de la interfaz donde se pierde más capacidad |
| `latencia_coordinacion` | Velocidad de ajuste de cooling y energía ante cambios de workload |
| `auto_cuantificacion` | Conocimiento de la stranded capacity propia |
| `bloqueantes` | Obstáculos organizacionales o técnicos que impiden la resolución |

### Conexión manual

```bash
psql -h localhost -U nlr -d nlr_diagnostic
```

### Reset completo de la DB (local)

```bash
psql -U postgres -c "DROP DATABASE IF EXISTS nlr_diagnostic;"
psql -U postgres -c "CREATE DATABASE nlr_diagnostic OWNER nlr;"
psql -U nlr -d nlr_diagnostic -f scripts/schema.sql
python scripts/seed_nlr.py
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
| `POSTGRES_MIN_POOL_SIZE`      | `2`                      | Conexiones mínimas del pool          |
| `POSTGRES_MAX_POOL_SIZE`      | `10`                     | Conexiones máximas del pool          |
| `RATE_LIMIT_REQUESTS`         | `60`                     | Requests permitidos por ventana      |
| `RATE_LIMIT_WINDOW_SECONDS`   | `60`                     | Duración de la ventana (segundos)    |
| `CORS_ORIGINS`                | `["http://localhost:3000"]` | Orígenes permitidos para CORS    |
| `PDF_SERVICE_URL`             | `http://localhost:3001`  | URL del microservicio Puppeteer      |
| `PDF_SERVICE_TIMEOUT_SECONDS` | `30`                     | Timeout para generación de PDF       |
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

## Microservicio Puppeteer (PDF)

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
      {"question_id": "st_01", "value": 4},
      {"question_id": "st_02", "value": 5},
      {"question_id": "ex_01", "value": 3}
    ]
  }'
```

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

Espera 60 segundos o ajusta `RATE_LIMIT_REQUESTS` en `.env`.

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
docker compose --profile seed run --rm seed
```

---

## Licencia

Proyecto interno — No Country.
