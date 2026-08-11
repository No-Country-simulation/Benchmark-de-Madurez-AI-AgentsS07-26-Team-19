import { create } from 'zustand'

import type { DiagnosticResponseV2 } from '@/types/diagnostic'

interface BenchmarkState {
  answers: Record<number, number>
  sessionId: string | null
  lastResult: DiagnosticResponseV2 | null
  setAnswer: (questionId: number, value: number) => void
  setSessionId: (sessionId: string | null) => void
  setLastResult: (result: DiagnosticResponseV2) => void
  clear: () => void
}

export const useBenchmarkStore = create<BenchmarkState>((set) => ({
  answers: {},
  sessionId: null,
  lastResult: null,
  setAnswer: (questionId, value) =>
    set((state) => ({ answers: { ...state.answers, [questionId]: value } })),
  setSessionId: (sessionId) => set({ sessionId }),
  setLastResult: (lastResult) => set({ lastResult }),
  clear: () => set({ answers: {}, sessionId: null }),
}))