-- NLR Diagnostic — PostgreSQL schema
-- Run: psql -U nlr -d nlr_diagnostic -f schema.sql

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
CREATE TABLE IF NOT EXISTS benchmark_scores (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dimension   VARCHAR(50) NOT NULL,
    score       NUMERIC(5,2) NOT NULL CHECK (score >= 0 AND score <= 100),
    source      VARCHAR(100) DEFAULT 'nlr_seed',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scores_dimension ON benchmark_scores (dimension);

-- Precomputed percentile buckets
CREATE TABLE IF NOT EXISTS benchmark_percentiles (
    id          SERIAL PRIMARY KEY,
    dimension   VARCHAR(50) NOT NULL,
    score_bucket NUMERIC(5,2) NOT NULL,
    percentile  NUMERIC(5,2) NOT NULL CHECK (percentile >= 0 AND percentile <= 100),
    UNIQUE (dimension, score_bucket)
);

CREATE INDEX IF NOT EXISTS idx_percentiles_dim_bucket
    ON benchmark_percentiles (dimension, score_bucket);

-- Dynamic dimension weights
CREATE TABLE IF NOT EXISTS benchmark_weights (
    dimension   VARCHAR(50) PRIMARY KEY,
    weight      NUMERIC(5,4) NOT NULL CHECK (weight >= 0 AND weight <= 1),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- User diagnostics
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

-- Seed default equal weights
INSERT INTO benchmark_weights (dimension, weight) VALUES
    ('strategic_thinking', 0.2000),
    ('execution',          0.2000),
    ('leadership',         0.2000),
    ('innovation',         0.2000),
    ('collaboration',      0.2000)
ON CONFLICT (dimension) DO NOTHING;
