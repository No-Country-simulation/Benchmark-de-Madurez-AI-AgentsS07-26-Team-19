-- ============================================================
-- Benchmark de Madurez AI Agents — DDL v2 (PostgreSQL)
-- Versión: refactor del esquema con FKs, TIMESTAMPTZ y checks
-- Ejecutar: psql -U nlr -d nlr_diagnostic -f scripts/schema-v2.sql
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ------------------------------------------------------------
-- 1) question — todas las preguntas del benchmark
-- ------------------------------------------------------------
CREATE TABLE question (
    id          SERIAL PRIMARY KEY,
    dimension   VARCHAR(50)     NOT NULL,
    question    TEXT            NOT NULL,
    description TEXT,
    type        VARCHAR(20)     NOT NULL,   -- single_choice | multiple_choice | text | numeric
    options     JSONB,
    weight      NUMERIC(5,2)    DEFAULT 1.00 CHECK (weight >= 0),
    order_index INT,
    is_active   BOOLEAN         DEFAULT TRUE,
    created_at  TIMESTAMPTZ     DEFAULT now()
);

COMMENT ON TABLE question IS 'Todas las preguntas de la encuesta, agrupadas por dimensión.';
COMMENT ON COLUMN question.dimension IS 'Dimensión a la que pertenece la pregunta';
COMMENT ON COLUMN question.type IS 'Tipo de pregunta (ej. single_choice, multiple_choice, text, numeric)';
COMMENT ON COLUMN question.options IS 'Opciones en formato JSONB para preguntas de selección';
COMMENT ON COLUMN question.weight IS 'Peso relativo de la pregunta en el cálculo del score';

-- ------------------------------------------------------------
-- 2) benchmark_response — encuesta completada de forma anónima
-- ------------------------------------------------------------
CREATE TABLE benchmark_response (
    id              SERIAL PRIMARY KEY,
    anonymous_code  VARCHAR(32) UNIQUE NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ
);

COMMENT ON TABLE benchmark_response IS 'Representa una encuesta completada de forma anónima por un operador.';
COMMENT ON COLUMN benchmark_response.anonymous_code IS 'Código anónimo único por respuesta';

-- ------------------------------------------------------------
-- 3) response_answer — respuestas a cada pregunta de una encuesta
-- ------------------------------------------------------------
CREATE TABLE response_answer (
    id          SERIAL PRIMARY KEY,
    response_id INT           NOT NULL,
    question_id INT           NOT NULL,
    answer      TEXT,
    score       NUMERIC(5,2)  CHECK (score >= 0 AND score <= 100),
    created_at  TIMESTAMPTZ   DEFAULT now(),
    CONSTRAINT fk_response
        FOREIGN KEY (response_id) REFERENCES benchmark_response (id) ON DELETE CASCADE,
    CONSTRAINT fk_question
        FOREIGN KEY (question_id) REFERENCES question (id) ON DELETE RESTRICT,
    CONSTRAINT uq_response_question UNIQUE (response_id, question_id)
);

COMMENT ON TABLE response_answer IS 'Respuestas a cada pregunta de una encuesta específica.';
COMMENT ON COLUMN response_answer.score IS 'Score normalizado por pregunta (0-100)';

-- ------------------------------------------------------------
-- 4) benchmark_result — resultados calculados por encuesta
-- ------------------------------------------------------------
CREATE TABLE benchmark_result (
    id                    SERIAL PRIMARY KEY,
    response_id           INT           NOT NULL UNIQUE,
    visibility_score      NUMERIC(5,2)  CHECK (visibility_score >= 0 AND visibility_score <= 100),
    friction_score        NUMERIC(5,2)  CHECK (friction_score >= 0 AND friction_score <= 100),
    latency_score         NUMERIC(5,2)  CHECK (latency_score >= 0 AND latency_score <= 100),
    quantification_score  NUMERIC(5,2)  CHECK (quantification_score >= 0 AND quantification_score <= 100),
    blockers_score        NUMERIC(5,2)  CHECK (blockers_score >= 0 AND blockers_score <= 100),
    overall_score         NUMERIC(5,2)  CHECK (overall_score >= 0 AND overall_score <= 100),
    overall_percentile    NUMERIC(5,2)  CHECK (overall_percentile >= 0 AND overall_percentile <= 100),
    ai_analysis           TEXT,
    created_at            TIMESTAMPTZ   DEFAULT now(),
    CONSTRAINT fk_result_response
        FOREIGN KEY (response_id) REFERENCES benchmark_response (id) ON DELETE CASCADE
);

COMMENT ON TABLE benchmark_result IS 'Resultados calculados para cada encuesta con scores por dimensión, score general, percentil y análisis IA.';

-- ------------------------------------------------------------
-- 5) public_dataset — datos públicos de referencia inicial
-- ------------------------------------------------------------
CREATE TABLE public_dataset (
    id                    SERIAL PRIMARY KEY,
    source                VARCHAR(100)  NOT NULL,
    source_type           VARCHAR(50),
    visibility_score      NUMERIC(5,2)  CHECK (visibility_score >= 0 AND visibility_score <= 100),
    friction_score        NUMERIC(5,2)  CHECK (friction_score >= 0 AND friction_score <= 100),
    latency_score         NUMERIC(5,2)  CHECK (latency_score >= 0 AND latency_score <= 100),
    quantification_score  NUMERIC(5,2)  CHECK (quantification_score >= 0 AND quantification_score <= 100),
    blockers_score        NUMERIC(5,2)  CHECK (blockers_score >= 0 AND blockers_score <= 100),
    overall_score         NUMERIC(5,2)  CHECK (overall_score >= 0 AND overall_score <= 100),
    collected_at          TIMESTAMPTZ,
    created_at            TIMESTAMPTZ   DEFAULT now()
);

COMMENT ON TABLE public_dataset IS 'Datos públicos utilizados como referencia inicial del benchmark.';

-- ------------------------------------------------------------
-- 6) rebalance_config — configuración del rebalanceo dinámico
-- ------------------------------------------------------------
CREATE TABLE rebalance_config (
    id              SERIAL PRIMARY KEY,
    min_responses   INT         DEFAULT 0 CHECK (min_responses >= 0),
    max_responses   INT         DEFAULT NULL CHECK (max_responses IS NULL OR max_responses >= min_responses),
    public_weight   NUMERIC(5,2) DEFAULT 0.50 CHECK (public_weight >= 0 AND public_weight <= 1),
    primary_weight  NUMERIC(5,2) DEFAULT 0.50 CHECK (primary_weight >= 0 AND primary_weight <= 1),
    description     TEXT,
    updated_at      TIMESTAMPTZ  DEFAULT now(),
    -- CHECK añadido: los pesos públicos + primarios deben sumar 1 (100%)
    CONSTRAINT chk_weights_sum CHECK (public_weight + primary_weight = 1)
);

COMMENT ON TABLE rebalance_config IS 'Configuración del rebalanceo dinámico entre datos públicos y datos primarios según la cantidad de respuestas.';

-- ------------------------------------------------------------
-- Índices recomendados
-- ------------------------------------------------------------
CREATE INDEX idx_question_dimension   ON question (dimension);
CREATE INDEX idx_response_created_at  ON benchmark_response (created_at);
CREATE INDEX idx_answer_question      ON response_answer (question_id);
CREATE INDEX idx_publicdataset_source ON public_dataset (source);

-- ------------------------------------------------------------
-- Vista resumida de scores por respuesta
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW vw_response_scores AS
SELECT
    r.id AS response_id,
    br.overall_score,
    br.overall_percentile,
    br.created_at AS result_created_at,
    r.created_at  AS response_created_at,
    r.completed_at
FROM benchmark_response r
LEFT JOIN benchmark_result br ON br.response_id = r.id;

COMMENT ON VIEW vw_response_scores IS 'Vista resumida que une respuestas con sus resultados calculados';