import { expect, test } from '@playwright/test'

test('overview cards match real database aggregates through the proxy', async ({ page, request }) => {
  const response = await request.get('/api-proxy/api/v1/inquiries/stats')
  expect(response.ok()).toBeTruthy()
  const stats = await response.json()
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Workspace overview' })).toBeVisible()
  await expect(page.locator('.metric-value').first()).toHaveText(new Intl.NumberFormat('en-US').format(stats.total))
  await expect(page.locator('.metric-value').nth(1)).toHaveText(new Intl.NumberFormat('en-US').format(stats.high_priority))
  await expect(page.locator('.connection')).toHaveText('Connected')
  expect(errors).toEqual([])
})

test('inquiry detail uses the existing read endpoint and Escape closes it', async ({ page, request }) => {
  const response = await request.get('/api-proxy/api/v1/inquiries/page?limit=1')
  expect(response.ok()).toBeTruthy()
  const data = await response.json()
  test.skip(data.items.length === 0, 'Live database has no inquiries to inspect.')
  const inquiry = data.items[0]
  await page.goto(`/inquiries?selected=${inquiry.id}`)
  const dialog = page.getByRole('dialog')
  await expect(dialog.getByRole('heading', { name: inquiry.customer_name, exact: true })).toBeVisible()
  await expect(dialog.getByText(inquiry.message, { exact: true })).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(dialog).not.toBeVisible()
  await expect(page).toHaveURL(/\/inquiries$/)
})

test('mobile navigation and layout work with the real service', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Workspace overview' })).toBeVisible()
  await page.getByRole('button', { name: 'Open navigation' }).click()
  await page.locator('nav').getByRole('link', { name: /Inquiries/ }).click()
  await expect(page.getByRole('heading', { name: 'All inquiries' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Open navigation' })).toHaveAttribute('aria-expanded', 'false')
  await expect(page.locator('.sidebar')).toBeHidden()
  await expect(page.locator('.inbox-panel [aria-busy]')).toHaveAttribute('aria-busy', 'false')
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
})

// Isolated browser-state fixtures exist only in this test file, never in app views.
const inquiry = {
  id: '00000000-0000-0000-0000-000000000001', customer_name: 'Test Customer',
  email: 'test@example.com', message: 'A browser test message.', category: 'sales',
  priority: 'high', status: 'new', ai_summary: 'Browser test summary.',
  created_at: '2026-01-01T12:00:00Z',
}

test('filters, sorting, and pagination update server query parameters', async ({ page }) => {
  await page.route('**/api/v1/inquiries/page?*', async (route) => {
    const params = new URL(route.request().url()).searchParams
    await route.fulfill({ json: { items: [inquiry], total: 41, limit: Number(params.get('limit')), offset: Number(params.get('offset')) } })
  })
  await page.goto('/inquiries')
  await page.getByLabel('Category', { exact: true }).selectOption('sales')
  await expect(page).toHaveURL(/category=sales/)
  await page.getByRole('button', { name: 'Priority', exact: true }).click()
  await expect(page).toHaveURL(/sort_by=priority/)
  await page.getByRole('button', { name: 'Next page' }).click()
  await expect(page).toHaveURL(/offset=20/)
  await page.getByLabel('Search inquiries').fill('Test Customer')
  await expect(page).toHaveURL(/search=Test\+Customer/)
  await expect(page).not.toHaveURL(/offset=/)
})

test('empty results and request failures offer recovery', async ({ page }) => {
  await page.route('**/api/v1/inquiries/page?*', (route) => route.fulfill({ status: 503, json: {} }))
  await page.goto('/inquiries?search=no-match')
  await expect(page.getByRole('heading', { name: 'Could not load inquiries' })).toBeVisible()
  await page.unroute('**/api/v1/inquiries/page?*')
  await page.route('**/api/v1/inquiries/page?*', (route) => route.fulfill({ json: { items: [], total: 0, limit: 20, offset: 0 } }))
  await page.getByRole('button', { name: 'Try again', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'No matching inquiries' })).toBeVisible()
  await page.getByRole('button', { name: 'Clear filters', exact: true }).last().click()
  await expect(page.getByRole('heading', { name: 'Your inbox is ready' })).toBeVisible()
})

test('loading state is announced while a page request is pending', async ({ page }) => {
  let release!: () => void
  const gate = new Promise<void>((resolve) => { release = resolve })
  await page.route('**/api/v1/inquiries/page?*', async (route) => {
    await gate
    await route.fulfill({ json: { items: [], total: 0, limit: 20, offset: 0 } })
  })
  await page.goto('/inquiries')
  await expect(page.getByRole('heading', { name: 'Loading inquiries', exact: true })).toBeVisible()
  release()
  await expect(page.getByRole('heading', { name: 'Your inbox is ready' })).toBeVisible()
})
