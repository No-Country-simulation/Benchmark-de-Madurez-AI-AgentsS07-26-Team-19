import type { Dimension, WeightsResponse } from './benchmark'

export interface DiagnosticAnswer {
  question_id: number
  value: 1 | 2 | 3 | 4 | 5
}

export interface DimensionScore {
  dimension: Dimension
  score: number
  percentile: number | null
}

export interface DiagnosticResult {
  id: number
  session_id: string
  overall_score: number
  dimensions: DimensionScore[]
  created_at: string
  ai_analysis?: string | null
}

export interface DiagnosticFrictionProfile {
  dominant_dimension: string
  score: number
  interpretation: string
}

export interface DiagnosticResponseV2 {
  diagnostic: DiagnosticResult
  perfil_friccion: DiagnosticFrictionProfile
  cuartil_superior: boolean
  pesos: WeightsResponse
  message: string
}