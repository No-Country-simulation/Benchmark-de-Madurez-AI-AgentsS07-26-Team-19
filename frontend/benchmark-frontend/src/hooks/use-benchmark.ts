import { useMutation, useQuery } from '@tanstack/react-query'

import {
  fetchAiHealth,
  fetchApiHealth,
  fetchPercentiles,
  fetchQuestions,
  fetchStats,
  fetchWeights,
  lookupPercentile,
} from '@/services/benchmark.service'
import { fetchDiagnostic } from '@/services/diagnostic.service'
import type { Dimension } from '@/types/benchmark'

export function useBenchmarkQuestions() {
  return useQuery({
    queryKey: ['benchmark', 'questions'],
    queryFn: ({ signal }) => fetchQuestions(signal),
  })
}

export function useBenchmarkStats() {
  return useQuery({
    queryKey: ['benchmark', 'stats'],
    queryFn: ({ signal }) => fetchStats(signal),
  })
}

export function useBenchmarkWeights() {
  return useQuery({
    queryKey: ['benchmark', 'weights'],
    queryFn: ({ signal }) => fetchWeights(signal),
  })
}

export function useBenchmarkPercentiles() {
  return useQuery({
    queryKey: ['benchmark', 'percentiles'],
    queryFn: ({ signal }) => fetchPercentiles(signal),
  })
}

export function usePercentileLookup() {
  return useMutation({
    mutationFn: ({ dimension, score }: { dimension: Dimension; score: number }) =>
      lookupPercentile(dimension, score),
  })
}

export function useApiHealth() {
  return useQuery({
    queryKey: ['health', 'api'],
    queryFn: ({ signal }) => fetchApiHealth(signal),
    refetchInterval: 30_000,
    retry: 0,
  })
}

export function useAiHealth() {
  return useQuery({
    queryKey: ['health', 'ai'],
    queryFn: ({ signal }) => fetchAiHealth(signal),
    refetchInterval: 30_000,
    retry: 0,
  })
}

export function useDiagnosticResult(id: number | undefined) {
  return useQuery({
    queryKey: ['diagnostic', id],
    queryFn: () => fetchDiagnostic(id as number),
    enabled: Number.isFinite(id),
    refetchInterval: (query) => {
      const hasAnalysis = query.state.data?.ai_analysis?.trim().length
      return hasAnalysis ? false : 4_000
    },
  })
}