-- NLR Diagnostic -- PostgreSQL schema
-- Run: psql -U nlr -d nlr_diagnostic -f schema.sql
--
-- Domain: data-center maturity benchmark
-- Five dimensions:
--   visibilidad_cross_layer, atribucion_friccion, latencia_coordinacion,
--   auto_cuantificacion, bloqueantes

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Benchmark questions (NLR dataset)
CREATE TABLE IF NOT EXISTS benchmark_questions (
    id          VARCHAR(50) PRIMARY KEY,
    dimension   VARCHAR(50) NOT NULL,
    text        TEXT NOT NULL,
    display_order INT NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_questions_dimension ON benchmark_questions (dimension);

-- Raw benchmark scores from population
-- source: 'nlr_seed' for synthetic public data, 'real' for actual submissions
CREATE TABLE IF NOT EXISTS benchmark_scores (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dimension   VARCHAR(50) NOT NULL,
    score       NUMERIC(5,2) NOT NULL CHECK (score >= 0 AND score <= 100),
    source      VARCHAR(100) DEFAULT 'nlr_seed',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scores_dimension ON benchmark_scores (dimension);
CREATE INDEX IF NOT EXISTS idx_scores_source ON benchmark_scores (source);

-- Precomputed percentile buckets (refreshed periodically by refresh_percentile_cache)
CREATE TABLE IF NOT EXISTS benchmark_percentiles (
    id          SERIAL PRIMARY KEY,
    dimension   VARCHAR(50) NOT NULL,
    score_bucket NUMERIC(5,2) NOT NULL,
    percentile  NUMERIC(5,2) NOT NULL CHECK (percentile >= 0 AND percentile <= 100),
    UNIQUE (dimension, score_bucket)
);

CREATE INDEX IF NOT EXISTS idx_percentiles_dim_bucket
    ON benchmark_percentiles (dimension, score_bucket);

-- Dynamic dimension weights (updated by rebalancing background task)
CREATE TABLE IF NOT EXISTS benchmark_weights (
    dimension   VARCHAR(50) PRIMARY KEY,
    weight      NUMERIC(5,4) NOT NULL CHECK (weight >= 0 AND weight <= 1),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Rebalancing state: tracks real response count and resulting weights over time
-- Append-only log; current state = row with highest id
CREATE TABLE IF NOT EXISTS rebalancing_config (
    id          SERIAL PRIMARY KEY,
    real_count  INT NOT NULL DEFAULT 0,
    real_weight NUMERIC(5,4) NOT NULL DEFAULT 0.0000,
    pub_weight  NUMERIC(5,4) NOT NULL DEFAULT 1.0000,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Anonymous user diagnostics
-- No PII is stored: session_id is a random token, no IP or user data.
CREATE TABLE IF NOT EXISTS diagnostics (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id       VARCHAR(128) NOT NULL,
    overall_score    NUMERIC(5,2) NOT NULL,
    dimension_scores JSONB NOT NULL DEFAULT '{}',
    answers          JSONB NOT NULL DEFAULT '[]',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_diagnostics_session ON diagnostics (session_id);
CREATE INDEX IF NOT EXISTS idx_diagnostics_created ON diagnostics (created_at DESC);

-- Seed default equal weights for data-center dimensions
INSERT INTO benchmark_weights (dimension, weight) VALUES
    ('visibilidad_cross_layer', 0.2000),
    ('atribucion_friccion',     0.2000),
    ('latencia_coordinacion',   0.2000),
    ('auto_cuantificacion',     0.2000),
    ('bloqueantes',             0.2000)
ON CONFLICT (dimension) DO NOTHING;

-- Seed initial rebalancing config (0 real responses, all weight on public)
INSERT INTO rebalancing_config (real_count, real_weight, pub_weight)
SELECT 0, 0.0000, 1.0000
WHERE NOT EXISTS (SELECT 1 FROM rebalancing_config);
