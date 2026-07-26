const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:3333'

class ApiError extends Error {
  status: number
  /** Código estável vindo de `detail.code` no backend (ex.: 'code_invalid').
   *  A UI decide a mensagem por ele, não pelo status HTTP. */
  code: string | null = null
  detailMessage: string | null = null
  retryAfter: number | null = null

  constructor(status: number, message: string) {
    super(message)
    this.status = status
    this.name = 'ApiError'
    try {
      const detail = JSON.parse(message)?.detail
      if (detail && typeof detail === 'object') {
        this.code = detail.code ?? null
        this.detailMessage = detail.message ?? null
        this.retryAfter = detail.retry_after ?? null
      }
    } catch {
      // corpo não-JSON (ex.: 502 do nginx) — segue só com status/texto
    }
  }
}

async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const url = `${BASE_URL}${path}`
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })

  if (res.status === 204) return undefined as T

  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new ApiError(res.status, text || res.statusText)
  }

  return res.json()
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'POST', body: JSON.stringify(body) }),
  put: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
  delete: (path: string) => request<void>(path, { method: 'DELETE' }),
}

export { ApiError }
