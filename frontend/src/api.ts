export type Category = 'sales' | 'support' | 'other'
export type Priority = 'low' | 'medium' | 'high'
export type InquiryStatus = 'new' | 'in_progress' | 'resolved'
export type SortField = 'created_at' | 'customer_name' | 'priority'
export interface Inquiry {
  id: string
  customer_name: string
  email: string
  message: string
  category: Category | null
  priority: Priority
  status: InquiryStatus
  ai_summary: string | null
  created_at: string
}
export interface InquiryPage { items: Inquiry[]; total: number; limit: number; offset: number }
export interface Stats {
  total: number; high_priority: number; sales: number; support: number
  other: number; unclassified: number; new: number; in_progress: number; resolved: number
}
export interface InquiryQuery {
  limit: number
  offset: number
  search: string
  category: Category | 'unclassified' | ''
  priority: Priority | ''
  status: InquiryStatus | ''
  sort_by: SortField
  sort_dir: 'asc' | 'desc'
}
export const defaultQuery: InquiryQuery = {
  limit: 20, offset: 0, search: '', category: '', priority: '', status: '',
  sort_by: 'created_at', sort_dir: 'desc',
}

const base = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '')

export class ApiError extends Error {
  constructor(public status: number) {
    super(status === 404 ? 'This inquiry could not be found.'
      : status === 409 ? 'The status changed or this transition is not allowed. Reload the inquiry before trying again.'
      : status === 422 ? 'The request could not be validated. Check your input and try again.'
      : 'The inquiry service is unavailable. Please try again.')
  }
}

export async function request<T>(
  path: string, signal?: AbortSignal, options: Pick<RequestInit, 'method' | 'body'> = {},
): Promise<T> {
  const timeout = AbortSignal.timeout(15000)
  const response = await fetch(`${base}${path}`, {
    ...options,
    signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
    headers: { Accept: 'application/json', ...(options.body ? { 'Content-Type': 'application/json' } : {}) },
    credentials: 'omit',
  })
  if (!response.ok) throw new ApiError(response.status)
  return response.json() as Promise<T>
}

export function getPage(query: InquiryQuery, signal?: AbortSignal) {
  const params = new URLSearchParams()
  Object.entries(query).forEach(([key, value]) => {
    if (value !== '') params.set(key, String(value))
  })
  return request<InquiryPage>(`/api/v1/inquiries/page?${params}`, signal)
}
export const getStats = (signal?: AbortSignal) => request<Stats>('/api/v1/inquiries/stats', signal)
export const getInquiry = (id: string, signal?: AbortSignal) =>
  request<Inquiry>(`/api/v1/inquiries/${encodeURIComponent(id)}`, signal)
export const updateInquiryStatus = (
  id: string, status: InquiryStatus, expectedStatus: InquiryStatus, signal?: AbortSignal,
) => request<Inquiry>(`/api/v1/inquiries/${encodeURIComponent(id)}/status`, signal, {
  method: 'PATCH', body: JSON.stringify({ status, expected_status: expectedStatus }),
})

export function errorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message
    : 'Unable to connect to the inquiry service. Check your connection and try again.'
}
