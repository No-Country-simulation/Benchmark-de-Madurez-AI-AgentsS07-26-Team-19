<div align="center">

# Benchmark de Madurez AI Agents — NLR Diagnostic

### API de diagnóstico de liderazgo NLR: benchmark de madurez en 5 dimensiones, percentiles, rebalanceo dinámico y reportes PDF — para el reto de No Country sobre data centers modernos.

[![Python 3.12](https://img.shields.io/badge/Python_3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Docker](https://img.shields.io/badge/Docker_Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![Puppeteer](https://img.shields.io/badge/Puppeteer-40B5A4?style=for-the-badge&logo=puppeteer&logoColor=white)](https://pptr.dev)

[![API docs](https://img.shields.io/badge/API_DOCS-/docs-22c55e?style=flat-square)](http://localhost:8000/docs)
[![License](https://img.shields.io/badge/license-MIT-22c55e?style=flat-square)](LICENSE)

</div>

---

# ENGLISH VERSION

## Overview

This repository contains the solution for the **AI Agents Maturity Benchmark** challenge (No Country, Team 19): a startup in AI infrastructure needs the industry's most complete maturity benchmark for a critical problem in modern data centers — paid and powered capacity that produces nothing because the facility's physical and operational layers are not coordinated.

The delivered MVP is the **NLR Diagnostic Backend**: a FastAPI API for leadership maturity diagnosis that includes a benchmark engine, scoring across 5 dimensions, percentile calculation, dynamic rebalancing, and PDF report generation via a Puppeteer microservice.

## Features

- **Benchmark engine** — evaluates diagnostic answers against a reference dataset
- **Scoring in 5 dimensions**:
  - `strategic_thinking` — Strategic thinking
  - `execution` — Execution
  - `leadership` — Leadership
  - `innovation` — Innovation
  - `collaboration` — Collaboration
- **Percentile calculation** — precomputed percentile buckets with lookup endpoint
- **Dynamic rebalancing** — weights are rebalanced per dimension based on the population
- **PDF report generation** — HTML to PDF via an independent **Puppeteer** microservice
- **Docker Compose** orchestration — database, API and PDF service in one command
- **Seeded dataset** — 10 benchmark questions and 1000 reference scores via `seed_nlr.py`

## Tech Stack

| Technology | Purpose | Official docs |
|---|---|---|
| [Python 3.12](https://www.python.org) | Language | [Python docs](https://docs.python.org/3/) |
| [FastAPI](https://fastapi.tiangolo.com) | REST API | [FastAPI docs](https://fastapi.tiangolo.com/) |
| [PostgreSQL 16](https://www.postgresql.org) | Database (asyncpg pool) | [PostgreSQL docs](https://www.postgresql.org/docs/) |
| [Puppeteer](https://pptr.dev) | HTML → PDF microservice (Node) | [Puppeteer docs](https://pptr.dev) |
| [Docker Compose](https://docs.docker.com/compose/) | Service orchestration | [Compose docs](https://docs.docker.com/compose/) |
| [Pydantic](https://docs.pydantic.dev) | Request/response schemas | [Pydantic docs](https://docs.pydantic.dev/) |

## Architecture

```text
┌─────────────┐     ┌──────────────────────────────┐     ┌────────────────┐
│   Clients   │ ──► │  FastAPI (backend/app)       │ ──► │  PostgreSQL 16  │
│  (curl/UI)  │     │  diagnostic · benchmark      │     │  benchmark_*    │
└─────────────┘     │  report · health             │     │  diagnostics    │
                    └──────────────┬───────────────┘     └────────────────┘
                                   │ HTTP
                    ┌──────────────▼───────────────┐
                    │  Puppeteer service (Node)    │
                    │  HTML → PDF reports (port 3001) │
                    └──────────────────────────────┘
```

- **API** — `backend/app` (FastAPI, asyncpg, pydantic-settings, rate limiting, structured logging)
- **PDF service** — `backend/puppeteer-service` (Node.js + Puppeteer, port 3001)
- **Database** — PostgreSQL 16 with precomputed percentile buckets; schema auto-applied in Docker via `docker-entrypoint-initdb.d`

## API Endpoints

Base URL: `http://localhost:8000/api/v1`

| Method | Route | Description |
|---|---|---|
| POST | `/diagnostic` | Submit test answers |
| GET | `/diagnostic/{id}` | Get result by ID |
| GET | `/benchmark/questions` | List benchmark questions |
| GET | `/benchmark/stats` | Statistics per dimension |
| GET | `/benchmark/percentiles` | Percentile table |
| POST | `/benchmark/percentiles/lookup` | Look up the percentile of a score |
| POST | `/report/pdf` | Generate PDF report |
| GET | `/health` | API health check |

Interactive docs at `http://localhost:8000/docs` once running.

## Getting Started

### Option A — Docker Compose (recommended)

```bash
docker compose up -d --build
docker compose --profile seed run --rm seed   # seed the NLR dataset
```

Services: `db` (5432) · `api` (8000) · `puppeteer` (3001)

### Option B — Local development

```bash
cd backend
python -m venv .venv && .\.venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt
copy .env.example .env
# create PostgreSQL user + database (see backend/README.md)
psql -U nlr -d nlr_diagnostic -f scripts/schema.sql
python scripts/seed_nlr.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> Complete setup instructions, env variables reference and troubleshooting: [`backend/README.md`](./backend/README.md)

### Tests

```bash
cd backend
pytest                      # run all tests
pytest --cov=app --cov-report=term-missing   # with coverage
```

## Official Documentation

- [FastAPI docs](https://fastapi.tiangolo.com/) — the framework reference
- [PostgreSQL docs](https://www.postgresql.org/docs/) — database reference
- [Puppeteer docs](https://pptr.dev) — HTML to PDF generation
- [Docker Compose docs](https://docs.docker.com/compose/) — orchestration
- [Pydantic docs](https://docs.pydantic.dev/) — data validation
- [asyncpg docs](https://magicstack.github.io/asyncpg/current/) — PostgreSQL driver

## Author

**Fernando Rodríguez López** — [GitHub](https://github.com/FerLpz55) · [LinkedIn](https://www.linkedin.com/in/ferlpz445/) · Team 19, No Country (AI Agents Maturity Benchmark)

---

# VERSIÓN EN ESPAÑOL

## Descripción General

Este repositorio contiene la solución del reto **Benchmark de Madurez de Agentes de IA** (No Country, Equipo 19): una startup de infraestructura de IA necesita el benchmark de madurez más completo de la industria sobre un problema crítico de los data centers modernos — la capacidad pagada y encendida que no produce nada porque las capas físicas y operativas del facility no se coordinan entre sí.

El MVP entregado es el **Backend de Diagnóstico NLR**: una API FastAPI para diagnóstico de madurez de liderazgo que incluye motor de benchmark, scoring en 5 dimensiones, cálculo de percentiles, rebalanceo dinámico y generación de reportes PDF vía un microservicio de Puppeteer.

## Características

- **Motor de benchmark** — evalúa las respuestas del diagnóstico contra un dataset de referencia
- **Scoring en 5 dimensiones**:
  - `strategic_thinking` — Pensamiento estratégico
  - `execution` — Ejecución
  - `leadership` — Liderazgo
  - `innovation` — Innovación
  - `collaboration` — Colaboración
- **Cálculo de percentiles** — buckets precalculados con endpoint de consulta
- **Rebalanceo dinámico** — los pesos se rebalancean por dimensión según la población
- **Generación de reportes PDF** — HTML a PDF vía un microservicio independiente de **Puppeteer**
- **Orquestación con Docker Compose** — base de datos, API y servicio PDF con un solo comando
- **Dataset sembrado** — 10 preguntas del benchmark y 1000 scores de referencia vía `seed_nlr.py`

## Stack Tecnológico

| Tecnología | Propósito | Documentación oficial |
|---|---|---|
| [Python 3.12](https://www.python.org) | Lenguaje | [Python docs](https://docs.python.org/3/) |
| [FastAPI](https://fastapi.tiangolo.com) | API REST | [FastAPI docs](https://fastapi.tiangolo.com/) |
| [PostgreSQL 16](https://www.postgresql.org) | Base de datos (pool asyncpg) | [PostgreSQL docs](https://www.postgresql.org/docs/) |
| [Puppeteer](https://pptr.dev) | Microservicio HTML → PDF (Node) | [Puppeteer docs](https://pptr.dev) |
| [Docker Compose](https://docs.docker.com/compose/) | Orquestación de servicios | [Compose docs](https://docs.docker.com/compose/) |
| [Pydantic](https://docs.pydantic.dev) | Esquemas de request/response | [Pydantic docs](https://docs.pydantic.dev/) |

## Arquitectura

```text
┌─────────────┐     ┌──────────────────────────────┐     ┌────────────────┐
│   Clientes  │ ──► │  FastAPI (backend/app)       │ ──► │  PostgreSQL 16  │
│  (curl/UI)  │     │  diagnostic · benchmark      │     │  benchmark_*    │
└─────────────┘     │  report · health             │     │  diagnostics    │
                    └──────────────┬───────────────┘     └────────────────┘
                                   │ HTTP
                    ┌──────────────▼───────────────┐
                    │  Servicio Puppeteer (Node)   │
                    │  Reportes HTML → PDF (puerto 3001) │
                    └──────────────────────────────┘
```

- **API** — `backend/app` (FastAPI, asyncpg, pydantic-settings, rate limiting, logging estructurado)
- **Servicio PDF** — `backend/puppeteer-service` (Node.js + Puppeteer, puerto 3001)
- **Base de datos** — PostgreSQL 16 con buckets de percentiles precalculados; el schema se aplica automáticamente en Docker vía `docker-entrypoint-initdb.d`

## Endpoints de la API

Base URL: `http://localhost:8000/api/v1`

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/diagnostic` | Enviar respuestas del test |
| GET | `/diagnostic/{id}` | Obtener resultado por ID |
| GET | `/benchmark/questions` | Listar preguntas del benchmark |
| GET | `/benchmark/stats` | Estadísticas por dimensión |
| GET | `/benchmark/percentiles` | Tabla de percentiles |
| POST | `/benchmark/percentiles/lookup` | Buscar el percentil de un score |
| POST | `/report/pdf` | Generar reporte PDF |
| GET | `/health` | Estado del API |

Documentación interactiva en `http://localhost:8000/docs` una vez corriendo.

## Cómo Empezar

### Opción A — Docker Compose (recomendada)

```bash
docker compose up -d --build
docker compose --profile seed run --rm seed   # sembrar el dataset NLR
```

Servicios: `db` (5432) · `api` (8000) · `puppeteer` (3001)

### Opción B — Desarrollo local

```bash
cd backend
python -m venv .venv && .\.venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt
copy .env.example .env
# crear usuario y base de datos de PostgreSQL (ver backend/README.md)
psql -U nlr -d nlr_diagnostic -f scripts/schema.sql
python scripts/seed_nlr.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> Instrucciones completas, referencia de variables de entorno y solución de problemas: [`backend/README.md`](./backend/README.md)

### Tests

```bash
cd backend
pytest                      # ejecutar todos los tests
pytest --cov=app --cov-report=term-missing   # con cobertura
```

## Documentación Oficial

- [FastAPI docs](https://fastapi.tiangolo.com/) — la referencia del framework
- [PostgreSQL docs](https://www.postgresql.org/docs/) — referencia de la base de datos
- [Puppeteer docs](https://pptr.dev) — generación de HTML a PDF
- [Docker Compose docs](https://docs.docker.com/compose/) — orquestación
- [Pydantic docs](https://docs.pydantic.dev/) — validación de datos
- [asyncpg docs](https://magicstack.github.io/asyncpg/current/) — driver de PostgreSQL

## Autor

**Fernando Rodríguez López** — [GitHub](https://github.com/FerLpz55) · [LinkedIn](https://www.linkedin.com/in/ferlpz445/) · Equipo 19, No Country (Benchmark de Madurez de Agentes de IA)
