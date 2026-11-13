import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { defaultQuery } from '../src/api'
import { useInquiries } from '../src/stores/inquiries'

beforeEach(() => { setActivePinia(createPinia()) })
afterEach(() => { vi.unstubAllGlobals() })

it('loads actual response totals rather than calculating them from a page', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ items: [], total: 120, limit: 20, offset: 0 }))))
  const store = useInquiries()
  await store.loadPage(defaultQuery)
  expect(store.page?.total).toBe(120)
  expect(store.loading).toBe(false)
  expect(store.error).toBe('')
})

it('keeps a superseded request from replacing newer results', async () => {
  let resolveOld!: (value: Response) => void
  const old = new Promise<Response>((resolve) => { resolveOld = resolve })
  vi.stubGlobal('fetch', vi.fn().mockReturnValueOnce(old)
    .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], total: 2 }))))
  const store = useInquiries()
  const first = store.loadPage(defaultQuery)
  await store.loadPage({ ...defaultQuery, priority: 'high' })
  resolveOld(new Response(JSON.stringify({ items: [], total: 99 })))
  await first
  expect(store.page?.total).toBe(2)
})

it('shows an error instead of stale inquiry rows after a failure', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(new Response(JSON.stringify({ items: [], total: 5 })))
    .mockRejectedValueOnce(new TypeError('Network error')))
  const store = useInquiries()
  await store.loadPage(defaultQuery)
  await store.loadPage({ ...defaultQuery, category: 'support' })
  expect(store.page).toBe(null)
  expect(store.error).toContain('Unable to connect')
  expect(store.loading).toBe(false)
})

it('loads aggregate stats and exposes refresh failures', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(new Response(JSON.stringify({ total: 44, high_priority: 7, sales: 5, support: 8 })))
    .mockResolvedValueOnce(new Response('', { status: 503 })))
  const store = useInquiries()
  await store.loadStats()
  expect(store.stats?.total).toBe(44)
  expect(store.updatedAt).toBeInstanceOf(Date)
  await store.refresh()
  expect(store.statsError).toContain('unavailable')
  expect(store.statsLoading).toBe(false)
  expect(store.refreshKey).toBe(1)
})
