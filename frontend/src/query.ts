import type { LocationQuery } from 'vue-router'
import { defaultQuery } from './api'
import type { InquiryQuery } from './api'

export function parseQuery(query: LocationQuery): InquiryQuery {
  const value = (key: string) => typeof query[key] === 'string' ? query[key] as string : ''
  const choice = <T extends string>(key: string, options: readonly T[], fallback: T): T =>
    options.find((option) => option === value(key)) ?? fallback
  const offset = Number(value('offset'))
  return {
    ...defaultQuery,
    limit: Number(choice('limit', ['10', '20', '50', '100'], '20')),
    offset: Number.isSafeInteger(offset) && offset >= 0 ? offset : 0,
    search: value('search').slice(0, 200),
    category: choice('category', ['', 'sales', 'support', 'other', 'unclassified'], ''),
    priority: choice('priority', ['', 'low', 'medium', 'high'], ''),
    status: choice('status', ['', 'new', 'in_progress', 'resolved'], ''),
    sort_by: choice('sort_by', ['created_at', 'customer_name', 'priority'], 'created_at'),
    sort_dir: choice('sort_dir', ['asc', 'desc'], 'desc'),
  }
}
