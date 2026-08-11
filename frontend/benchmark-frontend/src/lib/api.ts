const API_BASE_URL =
  (import.meta.env.VITE_API_URL as string | undefined) ??
  'https://backend-navy-alpha-68.vercel.app'
const API_PREFIX = '/api/v1'

export class ApiError extends Error {
  readonly status: number
  readonly detail: unknown

  constructor(status: number, detail?: unknown) {
    const detailText = detail != null ? `: ${JSON.stringify(detail)}` : ''
    super(`HTTP ${status}${detailText}`)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

async function request<T>(
  path: string,
  init?: RequestInit,
  prefix = API_PREFIX,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${prefix}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  })

  if (!response.ok) {
    const body = await response.json().catch(() => undefined)
    const detail = (body as { detail?: unknown } | undefined)?.detail ?? body
    throw new ApiError(response.status, detail)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export const api = {
  get<T>(path: string, signal?: AbortSignal): Promise<T> {
    return request<T>(path, { method: 'GET', signal })
  },
  post<T>(path: string, body: unknown): Promise<T> {
    return request<T>(path, { method: 'POST', body: JSON.stringify(body) })
  },
  getRoot<T>(path: string, signal?: AbortSignal): Promise<T> {
    return request<T>(path, { method: 'GET', signal }, '')
  },
}