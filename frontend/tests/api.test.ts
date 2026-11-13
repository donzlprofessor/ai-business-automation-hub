import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, defaultQuery, getPage, request, updateInquiryStatus } from '../src/api'
import { parseQuery } from '../src/query'

afterEach(() => { vi.unstubAllGlobals() })

describe('typed API client', () => {
  it('sends status and expected status as JSON without credentials', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: 'in_progress' })))
    vi.stubGlobal('fetch', fetchMock)
    await updateInquiryStatus('test-id', 'in_progress', 'new')
    const [url, options] = fetchMock.mock.calls[0]!
    expect(url).toContain('/api/v1/inquiries/test-id/status')
    expect(options.method).toBe('PATCH')
    expect(JSON.parse(options.body)).toEqual({ status: 'in_progress', expected_status: 'new' })
    expect(options.headers['Content-Type']).toBe('application/json')
    expect(options.credentials).toBe('omit')
  })

  it('does not retry writes after a conflict', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('private response', { status: 409 }))
    vi.stubGlobal('fetch', fetchMock)
    await expect(updateInquiryStatus('test-id', 'in_progress', 'new')).rejects.toThrow('Reload the inquiry')
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('serializes filters and literal searches without losing special characters', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ items: [], total: 0 })))
    vi.stubGlobal('fetch', fetchMock)
    await getPage({ ...defaultQuery, search: 'Ada & 100%', priority: 'high', offset: 20 })
    const [url, options] = fetchMock.mock.calls[0]!
    const parsed = new URL(url as string)
    expect(parsed.searchParams.get('search')).toBe('Ada & 100%')
    expect(parsed.searchParams.get('priority')).toBe('high')
    expect(parsed.searchParams.get('offset')).toBe('20')
    expect(parsed.searchParams.has('category')).toBe(false)
    expect(options.credentials).toBe('omit')
  })

  it('reports failed requests without exposing server response details', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('private traceback', { status: 500 })))
    await expect(request('/api/v1/inquiries/stats')).rejects.toBeInstanceOf(ApiError)
    await expect(request('/api/v1/inquiries/stats')).rejects.not.toThrow('private traceback')
  })
})

describe('URL query state', () => {
  it('validates bookmarks and returns safe defaults for invalid values', () => {
    expect(parseQuery({ priority: 'urgent', limit: '999', offset: '-3', sort_by: 'email' })).toEqual(defaultQuery)
  })
  it('preserves supported filters, page size and sorting', () => {
    expect(parseQuery({ category: 'unclassified', status: 'resolved', limit: '50', offset: '50', sort_by: 'priority', sort_dir: 'asc' }))
      .toMatchObject({ category: 'unclassified', status: 'resolved', limit: 50, offset: 50, sort_by: 'priority', sort_dir: 'asc' })
  })
})
