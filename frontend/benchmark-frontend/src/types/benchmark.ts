export const DIMENSIONS = [
  'visibility',
  'friction',
  'latency',
  'quantification',
  'blockers',
] as const

export type Dimension = (typeof DIMENSIONS)[number]

export const DIMENSION_LABELS: Record<Dimension, string> = {
  visibility: 'Visibilidad',
  friction: 'Fricción',
  latency: 'Latencia',
  quantification: 'Cuantificación',
  blockers: 'Bloqueadores',
}

export interface BenchmarkQuestion {
  id: number
  dimension: Dimension
  text: string
  order: number
}

export interface BenchmarkStats {
  dimension: Dimension
  mean: number
  std_dev: number
  sample_size: number
}

export interface WeightsResponse {
  public_weight: number
  real_weight: number
  real_count: number
  updated_at: string | null
}

export type PercentileThresholds = Record<string, number>

export type PercentilesMap = Record<Dimension, PercentileThresholds>

export interface PercentileLookupResponse {
  dimension: Dimension
  score: number
  percentile: number
}

export type HealthStatus = 'ok' | 'unavailable'

export interface ApiHealthResponse {
  status: HealthStatus
  version: string
  environment: string
}

export interface AiHealthResponse {
  status: HealthStatus
}