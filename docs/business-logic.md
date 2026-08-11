# Lógica de negocio

Algoritmos centrales detrás del scoring, los percentiles, el rebalanceo y la
idempotencia.

---

## Las 5 dimensiones

Fuente única: `backend/app/core/dimensions.py` (`ORDERED_DIMENSIONS`).

| Dimensión | Significado |
|---|---|
| `visibility` | Vista unificada en tiempo real de energía, cooling y workloads |
| `friction` | La interfaz donde se pierde capacidad |
| `latency` | Velocidad de ajuste de cooling/energía ante cambios de workload |
| `quantification` | Conocimiento de la stranded capacity propia |
| `blockers` | Obstáculos organizacionales o técnicos que impiden resolver el problema |

---

## Flujo completo de POST /diagnostic

```mermaid
sequenceDiagram
    autonumber
    participant CL as Cliente
    participant API as api/v1/diagnostic.py
    participant ENG as benchmark_engine
    participant SC as scoring
    participant PC as percentiles
    participant RB as rebalancing
    participant AI as ai_client
    participant DB as PostgreSQL

    CL->>API: POST /diagnostic {session_id?, answers[]}
    API->>API: generate_anon_session_id() si hace falta<br/>(validar len <= 32)
    API->>API: compute_answers_fingerprint(answers)

    API->>ENG: get_questions(pool)
    ENG-->>API: mapa question_id -> Dimension

    API->>SC: compute_dimension_scores(answers, qmap)
    SC-->>API: list[DimensionScore] (0-100)

    API->>RB: get_current_weights(pool)
    RB-->>API: WeightsState

    API->>PC: calculate_percentiles_for_user(pool, scores, w_public, w_real)
    PC->>DB: SELECT public_dataset + benchmark_result (cache 30s)
    PC-->>API: percentil por dimensión

    API->>ENG: save_diagnostic_idempotent(pool, session_id, fingerprint, ...)
    Note over ENG,DB: pg_advisory_xact_lock(hashtext('diag:'+session_id))
    alt sin sesión existente
        ENG->>DB: INSERT benchmark_response + response_answer xN + benchmark_result
        ENG-->>API: DiagnosticOutcome(replayed=false)
    else mismo fingerprint
        ENG-->>API: DiagnosticOutcome(replayed=true) — sin escrituras
    else fingerprint distinto
        ENG-->>API: IdempotencyConflictError -> HTTP 409
    end

    opt solo si NO es replay
        API-->>RB: BackgroundTask: run_rebalancing(pool)
        API-->>AI: BackgroundTask: analyze(scores, overall)
        AI-->>ENG: update_ai_analysis(pool, response_id, markdown)
    end

    API-->>CL: 200 DiagnosticResponseV2
```

---

## Scoring

Definido en `backend/app/services/scoring.py`.

- Cada respuesta es 1-5. El score de dimensión es el promedio de sus respuestas
  normalizado a 0-100: `score = (promedio / 5) * 100` (`normalize_answer`,
  `core/dimensions.py`).
- Las dimensiones sin respuestas quedan en `0.0` (por diseño: el frontend envía
  respuestas para todas las preguntas activas).
- El overall es el promedio simple de los 5 scores de dimensión.
- El score normalizado por pregunta `(value / 5) * 100` también se guarda en
  `response_answer.score`.

---

## Percentiles en vuelo

Definido en `backend/app/services/percentiles.py`. No hay tabla precacheadas.

```mermaid
flowchart TD
    A(["calculate_percentiles_for_user"]) --> B["Por cada columna de dimensión<br/>(DIMENSION_SCORE_COLUMN)"]
    B --> C["_load_blended_scores (TTL 30s)"]
    C --> C1["SELECT score FROM public_dataset"]
    C --> C2["SELECT score FROM benchmark_result"]
    C1 --> M["weighted_merge(public, real, w_public, w_real)"]
    C2 --> M
    M --> S["muestreo: n_public = len(public)*w_public<br/>n_real = len(real)*w_real (random.sample)"]
    S --> P["calculate_percentile(user_score, merged)"]
    P --> R["percentiles[dimension] = valor"]
    R --> B
    B -->|las 5 listas| E(["mapa de percentiles"])
```

`calculate_percentile`: el score del usuario se agrega al dataset combinado
(`all_scores = combined_dataset + [user_score]`), se cuentan los scores
estrictamente menores a él (`s < user_score`), y se divide por el total de la
lista (`len(all_scores)` = tamaño del dataset + 1). Devuelve `50.0` si el
dataset mezclado está vacío. Los umbrales
(`compute_percentile_thresholds`) por defecto son P10/P25/P50/P75/P90/P99.

---

## Rebalanceo dinámico

Definido en `backend/app/services/rebalancing.py`. Fórmula de la issue #23:

```
si real_count < 20:  real_weight = real_count / 100
si no:               real_weight = 0.2 + (real_count - 20) * 0.004
real_weight = min(real_weight, 0.80)
public_weight = 1 - real_weight
```

```mermaid
flowchart TD
    A(["run_rebalancing(pool)"]) --> B["real_count = COUNT(*) FROM benchmark_response"]
    B --> C{"real_count < 20?"}
    C -->|sí| D["real_weight = real_count / 100"]
    C -->|no| E["real_weight = 0.2 + (real_count-20) * 0.004"]
    D --> F["tope: min(real_weight, 0.80)"]
    E --> F
    F --> G["public_weight = 1 - real_weight (redondeo 4dp)"]
    G --> H["UPSERT rebalance_config id=1 (fila única)<br/>chk_weights_sum: public + primary = 1"]
```

Notas:

- Corre como `BackgroundTask` tras cada diagnóstico **nuevo**.
- `real_weight` se guarda en la columna `primary_weight`.
- Las lecturas hacen fallback a `public_weight=1.0`, `real_weight=0.0` cuando no
  hay fila guardada.
- `real_count < 0` lanza `ValueError`.

---

## Idempotencia

Estilo Stripe: `session_id` actúa como Idempotency-Key.

```mermaid
flowchart TD
    A(["save_diagnostic_idempotent"]) --> L["pg_advisory_xact_lock(hashtext('diag:'+session_id))"]
    L --> E{"¿existe por session_id?"}
    E -->|no| I["INSERT response + answers + result (una tx)"]
    I --> N["DiagnosticOutcome(replayed=false)"]
    E -->|sí| F{"¿stored fingerprint == nuevo fingerprint?"}
    F -->|igual| R["DiagnosticOutcome(replayed=true)"]
    F -->|distinto| C["IdempotencyConflictError -> HTTP 409"]
```

- Fingerprint = SHA-256 sobre los pares `(question_id, value)` **ordenados** —
  reordenar respuestas no cambia el resultado (`idempotency.py`).
- La concurrencia se serializa con un advisory lock de PostgreSQL con alcance de
  transacción.
- En un replay no se escriben filas ni corren efectos en background; la respuesta
  refleja el diagnóstico guardado + los percentiles **actuales**.
- La restricción `UNIQUE` de `benchmark_response.anonymous_code` mantiene el
  anonimato y la unicidad.