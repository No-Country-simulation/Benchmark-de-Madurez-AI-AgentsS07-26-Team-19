import { api } from '@/lib/api'
import type {
  AiHealthResponse,
  ApiHealthResponse,
  BenchmarkQuestion,
  BenchmarkStats,
  PercentileLookupResponse,
  PercentilesMap,
  WeightsResponse,
} from '@/types/benchmark'
import type { Dimension } from '@/types/benchmark'

export function fetchQuestions(signal?: AbortSignal): Promise<BenchmarkQuestion[]> {
  return api.get<BenchmarkQuestion[]>('/benchmark/questions', signal)
}

export function fetchStats(signal?: AbortSignal): Promise<BenchmarkStats[]> {
  return api.get<BenchmarkStats[]>('/benchmark/stats', signal)
}

export function fetchWeights(signal?: AbortSignal): Promise<WeightsResponse> {
  return api.get<WeightsResponse>('/benchmark/weights', signal)
}

export function fetchPercentiles(signal?: AbortSignal): Promise<PercentilesMap> {
  return api.get<PercentilesMap>('/benchmark/percentiles', signal)
}

export function lookupPercentile(
  dimension: Dimension,
  score: number,
): Promise<PercentileLookupResponse> {
  return api.post<PercentileLookupResponse>('/benchmark/percentiles/lookup', {
    dimension,
    score,
  })
}

export function fetchApiHealth(signal?: AbortSignal): Promise<ApiHealthResponse> {
  return api.getRoot<ApiHealthResponse>('/health', signal)
}

export function fetchAiHealth(signal?: AbortSignal): Promise<AiHealthResponse> {
  return api.getRoot<AiHealthResponse>('/health/ai', signal)
}