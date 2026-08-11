import { api } from '@/lib/api'
import type { ReportPdfResponse } from '@/types/report'

export function generateReportPdf(
  diagnosticId: number,
  htmlContent?: string | null,
): Promise<ReportPdfResponse> {
  return api.post<ReportPdfResponse>('/report/pdf', {
    diagnostic_id: diagnosticId,
    html_content: htmlContent ?? null,
  })
}

export function downloadReportPdf(pdfBase64: string, filename: string): void {
  const bytes = Uint8Array.from(atob(pdfBase64), (char) => char.charCodeAt(0))
  const blob = new Blob([bytes], { type: 'application/pdf' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}