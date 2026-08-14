# Referencia de la API

URL base: `http://localhost:8000/api/v1`

Todas las rutas `/api/v1` tienen rate limit (default `60/60second`, slowapi
moving-window, por IP del cliente). Ver `core/security.py`.

Todas las respuestas de error siguen el formato estándar de FastAPI:
`{"detail": "<mensaje>"}`. El `429 Too Many Requests` usa el formato propio de
slowapi (no el formato FastAPI estándar).

---

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/diagnostic` | Enviar respuestas → resultado enriquecido |
| GET | `/diagnostic/{id}` | Obtener resultado guardado (con `ai_analysis`) |
| GET | `/benchmark/questions` | Preguntas activas del benchmark |
| GET | `/benchmark/stats` | Media, desviación y n por dimensión (mezclado) |
| GET | `/benchmark/percentiles` | Umbrales de percentil P10–P99 por dimensión |
| POST | `/benchmark/percentiles/lookup` | Percentil de un score en una dimensión |
| GET | `/benchmark/weights` | Pesos vigentes público vs real |
| POST | `/report/pdf` | Generar reporte PDF (501 sin servicio) |
| GET | `/health` | Estado de la API |
| GET | `/health/ai` | Sondeo del servicio IA (Ollama / HF) |

---

## `POST /diagnostic`

`POST /api/v1/diagnostic` — Envía un diagnóstico. Idempotente vía `session_id`.

### Request

```json
{
  "session_id": null,
  "answers": [
    { "question_id": 1, "value": 4 },
    { "question_id": 2, "value": 5 },
    { "question_id": 3, "value": 3 }
  ]
}
```

| Campo | Tipo | Notas |
|---|---|---|
| `session_id` | string? | Clave de idempotencia; si va `null`/omitido se genera uno aleatorio (`secrets.token_urlsafe(24)`, máximo 32 caracteres) |
| `answers` | `[{question_id:int, value:int}]` | `min_length=1`; `value` entre 1 y 5 |

### Respuesta `200 OK` (DiagnosticResponseV2)

```json
{
  "diagnostic": {
    "id": 1,
    "session_id": "abc...",
    "overall_score": 72.0,
    "dimensions": [
      { "dimension": "visibility", "score": 80.0, "percentile": 65.0 },
      { "dimension": "friction", "score": 50.0, "percentile": 40.0 },
      { "dimension": "latency", "score": 60.0, "percentile": 55.0 },
      { "dimension": "quantification", "score": 90.0, "percentile": 90.0 },
      { "dimension": "blockers", "score": 80.0, "percentile": 70.0 }
    ],
    "created_at": "2026-08-11T00:00:00Z",
    "ai_analysis": null
  },
  "perfil_friccion": {
    "dominant_dimension": "friction",
    "score": 50.0,
    "interpretation": "La dimensión con mayor fricción es friction con un score de 50.0/100."
  },
  "cuartil_superior": false,
  "pesos": {
    "public_weight": 1.0,
    "real_weight": 0.0,
    "real_count": 0,
    "updated_at": null
  },
  "message": "Diagnostic submitted successfully"
}
```

Notas:

- `perfil_friccion` = la dimensión con menor score (la fricción dominante).
- `cuartil_superior` = `true` cuando el **percentil real** del overall contra la
  población mezclada (público + real con los pesos vigentes) es ≥ P75 — no un
  umbral de score fijo (issue #44).
- `pesos` = los **mismos** pesos usados para el blend de percentiles (de `rebalance_config`).
- `ai_analysis` se completa luego por un `BackgroundTask` (se lee con `GET /diagnostic/{id}`).
- Los replays devuelven el resultado guardado con `message: "Diagnostic replayed from session"` y sin efectos secundarios.

### Errores

| Código | Condición |
|---|---|
| `409 Conflict` | Mismo `session_id` con respuestas distintas |
| `422` | `session_id` > 32 caracteres; `answers` vacío; `value` fuera de 1-5 |
| `429` | Rate limit superado |

### Efectos secundarios en background

Después de un diagnóstico **nuevo** (no replay):

1. `run_rebalancing(pool)` — recalcula los pesos público/real y hace upsert de `rebalance_config`.
2. `_generate_ai_analysis_task(...)` — llama al servicio IA y guarda `ai_analysis`; si falla solo loguea y deja `NULL`.

---

## `GET /diagnostic/{id}`

Devuelve un `DiagnosticResult`:

| Campo | Notas |
|---|---|
| `dimensions[].percentile` | Recomputed **en vuelo** contra la población mezclada con los pesos vigentes (issue #44) — mismo cálculo que el POST. No se persisten por fila en BD |

`404` si el id no existe.

---

## `/benchmark`

### `GET /benchmark/questions`

Devuelve `list[BenchmarkQuestion]`: `{id:int, dimension, text, order}` para
`is_active = TRUE` ordenadas por `order_index`.

### `GET /benchmark/stats`

`list[BenchmarkStats]` por dimensión: `{dimension, mean, std_dev, sample_size}`.
Mezcla `public_dataset` + `benchmark_result` con UNION ALL. Cache de 30s
(`_fetch_dimension_stats`).

### `GET /benchmark/percentiles`

`dict[dimensión → {percentil: umbral}]` sobre la población mezclada.
Los umbrales corresponden exactamente a los percentiles `[10, 25, 50, 75, 90, 99]`
computados por `compute_percentile_thresholds()` en `services/percentiles.py`.
Usa los pesos vigentes.

### `POST /benchmark/percentiles/lookup`

Body: `{"dimension": "visibility", "score": 70.0}` →
`{"dimension", "score", "percentile"}`. Usa los pesos vigentes.

### `GET /benchmark/weights`

`WeightsResponse`: `{public_weight, real_weight, real_count, updated_at}` —
estado vigente de la fila única; si no existe registro, fallback a 100% público.

---

## `/report/pdf`

`POST /api/v1/report/pdf`, body:

```json
{ "diagnostic_id": 1, "html_content": null }
```

- `200`: `{pdf_base64, filename}`
- `404` si el diagnóstico no existe.
- `501 Not Implemented` si `PDF_SERVICE_URL` está vacío (producción: el frontend imprime el PDF del lado del cliente).
- `502` si el servicio Puppeteer falla.

`html_content` opcional: si se provee se renderiza tal cual; si no, se genera un
HTML por defecto a partir de las columnas fijas de score del registro.

---

## Health

| Ruta | Respuesta |
|---|---|
| `GET /health` | `{status: "ok", version, environment}` |
| `GET /health/ai` | `{status: "ok"}` o `{status: "unavailable"}` (probe a `/v1/models` del servicio IA) |