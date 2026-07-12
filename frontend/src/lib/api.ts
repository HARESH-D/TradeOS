const API_BASE = import.meta.env.VITE_API_URL ?? '/api'

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message)
  }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('tradeos_token')
  const isFormData = options.body instanceof FormData
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...(!isFormData ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new ApiError(body.detail ?? 'Request failed', response.status)
  }
  return response.json() as Promise<T>
}
