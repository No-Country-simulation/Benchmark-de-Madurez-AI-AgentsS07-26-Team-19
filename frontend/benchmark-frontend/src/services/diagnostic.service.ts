import { api } from '@/lib/api'
import type { DiagnosticAnswer, DiagnosticResponseV2, DiagnosticResult } from '@/types/diagnostic'

export function fetchDiagnostic(id: number, signal?: AbortSignal): Promise<DiagnosticResult> {
  return api.get<DiagnosticResult>(`/diagnostic/${id}`, signal)
}

export function submitDiagnostic(
  answers: DiagnosticAnswer[],
  sessionId?: string | null,
): Promise<DiagnosticResponseV2> {
  return api.post<DiagnosticResponseV2>('/diagnostic', {
    session_id: sessionId ?? null,
    answers,
  })
}