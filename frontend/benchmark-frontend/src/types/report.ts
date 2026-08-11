export interface ReportPdfRequest {
  diagnostic_id: number
  html_content?: string | null
}

export interface ReportPdfResponse {
  pdf_base64?: string | null
  filename: string
}